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

func initFirestore(ctx context.Context) {
	firestoreClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_firebase.json")
		firestoreClient, err = firestore.NewClient(ctx, sa)
		if err != nil {
			log.Fatalf("firestore init error: %v\n", err)
		}
	})
}

func initPubSub(ctx context.Context) {
	pubsubClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_pub_sub.json")
		pubsubClient, err = pubsub.NewClient(ctx, projectId, sa)
		if err != nil {
			log.Fatalf("pubsub init error: %v", err)
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

func pubMissingVideoUrl(ctx context.Context, videoIds []string) error {
	req := &firestorepb.BatchGetDocumentsRequest{
		Database:  databaseUrl,
		Documents: mapIdsToDocuments(videoIds),
		Mask:      docMask,
	}
	t := time.Now()
	stream, err := firestoreClient.BatchGetDocuments(ctx, req)
	if err != nil {
		return fmt.Errorf("batch get documents error: %v", err)
	}
	log.Printf("batch get took %s", time.Since(t))

	t = time.Now()
	var results []*pubsub.PublishResult
	for {
		resp, err := stream.Recv()
		if err == io.EOF {
			break
		}
		if err != nil {
			return fmt.Errorf("stream recv error: %v", err)
		}

		missingPath := resp.GetMissing()
		lastSlashIndex := strings.LastIndex(missingPath, "/")

		if lastSlashIndex != -1 {
			videoUrl := fmt.Sprintf("https://www.youtube.com/watch?v=%s", missingPath[lastSlashIndex+1:])
			urls, _ := json.Marshal([1]string{videoUrl})
			result := topic.Publish(ctx, &pubsub.Message{
				Data: []byte(urls),
			})
			results = append(results, result)
		}
	}
	log.Printf("processing stream took %s", time.Since(t))

	// process all the results
	for _, r := range results {
		_, err := r.Get(ctx)
		if err != nil {
			return fmt.Errorf("pubsub processing error: %s", err)
		}
	}
	return nil
}

func pubMissingIds(ctx context.Context, e event.Event) error {
	initFirestore(ctx)
	initPubSub(ctx)

	// Process the msg and convert to golang slice of strings
	var msg MessagePublishedData
	if err := e.DataAs(&msg); err != nil {
		return fmt.Errorf("event.DataAs: %v", err)
	}

	jsonString := string(msg.Message.Data) // Automatically decoded from base64
	var videoIds []string
	if err := json.Unmarshal([]byte(jsonString), &videoIds); err != nil {
		return fmt.Errorf("json unmarshal error: %v", err)
	}

	t := time.Now()
	err := pubMissingVideoUrl(ctx, videoIds)
	log.Printf("handler took %s", time.Since(t))
	return err
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
