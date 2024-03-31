package function

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"os"
	"strings"
	"sync"
	"time"

	firestore "cloud.google.com/go/firestore/apiv1"
	firestorepb "cloud.google.com/go/firestore/apiv1/firestorepb"
	"cloud.google.com/go/pubsub"
	"google.golang.org/api/option"

	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
)

var (
	ctx = context.Background()

	// Environment Globals; setup in Cloud Build Triggers
	projectId    = os.Getenv("PROJECT_ID")
	databaseId   = os.Getenv("DATABASE_ID")
	documentPath = os.Getenv("DOCUMENT_PATH")

	// Firestore Globals
	firestoreClient           *firestore.Client
	firestoreClientLazyLoaded sync.Once // Ensure client loaded just once
	databaseUrl               = fmt.Sprintf("projects/%s/databases/%s", projectId, databaseId)
	docMask                   = &firestorepb.DocumentMask{FieldPaths: []string{}} // Do not get any fields, just check existence

	// PubSub Globals
	pubsubClient           *pubsub.Client
	pubsubClientLazyLoaded sync.Once
	topic                  *pubsub.Topic
	topic_name             = "YoutubeURLs"
)

type MessagePublishedData struct {
	Message PubSubMessage
}

type PubSubMessage struct {
	Data []byte `json:"data"`
}

func initFirestore() {
	firestoreClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_firebase.json")
		firestoreClient, err = firestore.NewClient(ctx, sa)
		if err != nil {
			log.Fatalln(err)
		}
	})
}

func initPubSub() {
	pubsubClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_pub_sub.json")
		pubsubClient, err = pubsub.NewClient(ctx, projectId, sa)
		if err != nil {
			log.Fatalln(err)
		}
		topic = pubsubClient.Topic(topic_name)
	})
}

func mapIdsToDocuments(videoIds []string) []string {
	documents := make([]string, len(videoIds))
	for i := range videoIds {
		documents[i] = fmt.Sprintf("projects/%s/databases/%s/documents/%s/%s",
			projectId,
			databaseId,
			documentPath,
			videoIds[i])
	}
	return documents
}

func pubMissingVideoUrl(videoIds []string) {
	req := &firestorepb.BatchGetDocumentsRequest{
		Database:  databaseUrl,
		Documents: mapIdsToDocuments(videoIds),
		Mask:      docMask,
	}
	t := time.Now()
	stream, err := firestoreClient.BatchGetDocuments(ctx, req)
	log.Printf("batch get took %s", time.Since(t))
	if err != nil {
		log.Fatalln(err)
	}

	t = time.Now()
	var results []*pubsub.PublishResult
	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			log.Fatalln(err)
		}

		missingPath := resp.GetMissing()
		lastSlashIndex := strings.LastIndex(missingPath, "/")

		if lastSlashIndex != -1 {
			videoUrl := fmt.Sprintf("https://www.youtube.com/watch?v=%s", missingPath[lastSlashIndex+1:])
			result := topic.Publish(ctx, &pubsub.Message{
				Data: []byte(videoUrl),
			})
			results = append(results, result)
		}
	}
	log.Printf("processing stream took %s", time.Since(t))

	// process all the results
	for _, r := range results {
		_, err := r.Get(ctx)
		if err != nil {
			log.Fatalln(err)
		}
	}
}

func pubMissingIds(ctx context.Context, e event.Event) error {
	initFirestore()
	initPubSub()

	// Process the msg and convert to golang slice of strings
	var msg MessagePublishedData
	if err := e.DataAs(&msg); err != nil {
		return fmt.Errorf("event.DataAs: %v", err)
	}

	jsonString := string(msg.Message.Data) // Automatically decoded from base64
	var videoIds []string
	if err := json.Unmarshal([]byte(jsonString), &videoIds); err != nil {
		log.Fatalf("JSON Unmarshal Error: %v", err)
	}

	t := time.Now()
	pubMissingVideoUrl(videoIds)
	log.Printf("handler took %s", time.Since(t))
	return nil
}

func init() {
	fixDir()

	functions.CloudEvent("PubMissingIds", pubMissingIds)
}

func fixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}