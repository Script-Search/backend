package function

import (
	"context"
	"log"
	"os"
	"sync"

	"cloud.google.com/go/pubsub"
	"google.golang.org/api/option"
)

var (
	// Environment Globals; setup in Cloud Build Triggers
	projectId = os.Getenv("PROJECT_ID")

	// PubSub Globals
	pubsubClient           *pubsub.Client
	pubsubClientLazyLoaded sync.Once
	topic                  *pubsub.Topic
	topic_name             = "SyncVideoBatch"
)

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
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
