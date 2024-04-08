package function

import (
	"context"
	"log"
	"os"
	"sync"
	"net"

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

	localAddr *net.UDPAddr
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
		topic.PublishSettings.CountThreshold = 1
		topic.PublishSettings.DelayThreshold = 0
	})
}

func DebugAddr() {
	conn, err := net.Dial("udp", "8.8.8.8:80")
	if err != nil {
		log.Fatalf("debugaddr init error: %v", err)
	}

     defer conn.Close()
     localAddr = conn.LocalAddr().(*net.UDPAddr)
}