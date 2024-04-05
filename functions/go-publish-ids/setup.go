package function

import (
	"context"
	"log"
	"os"
	"sync"
	"fmt"


	firestore "cloud.google.com/go/firestore/apiv1"
	firestorepb "cloud.google.com/go/firestore/apiv1/firestorepb"
	"cloud.google.com/go/pubsub"
	"google.golang.org/api/option"
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

	ID_BATCH_SIZE = 25
)

func InitFirestore(ctx context.Context) {
	firestoreClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_firebase.json")
		firestoreClient, err = firestore.NewClient(ctx, sa)
		if err != nil {
			log.Fatalf("firestore init error: %v\n", err)
		}
	})
}

func InitPubSub(ctx context.Context) {
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

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}
