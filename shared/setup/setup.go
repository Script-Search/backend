package setup

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	firestore "cloud.google.com/go/firestore/apiv1"
	"cloud.google.com/go/pubsub"
	"github.com/typesense/typesense-go/typesense"
	"google.golang.org/api/option"
)

type PubSubSetupInfo struct {
	ProjectId       string
	TopicName       string
	CredentialsFile string
}

type TypesenseSetupInfo struct {
	Hosts          []string
	Port           int
	APIKey         string
	TimeoutSeconds int
}

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}

func InitPubSub(ctx context.Context, psCLazyLoaded *sync.Once, topic *pubsub.Topic, setupInfo PubSubSetupInfo) {
	psCLazyLoaded.Do(func() {
		sa := option.WithCredentialsFile(setupInfo.CredentialsFile)
		psClient, err := pubsub.NewClient(ctx, setupInfo.ProjectId, sa)
		if err != nil {
			log.Fatalf("pubsub init error: %v", err)
		}
		topic = psClient.Topic(setupInfo.TopicName)
	})
}

func InitFirestore(ctx context.Context, fcLazyLoaded *sync.Once, fsClient *firestore.Client, credsFile string) {
	fcLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile(credsFile)
		fsClient, err = firestore.NewClient(ctx, sa)
		if err != nil {
			log.Fatalf("firestore init error: %v", err)
		}
	})
}

func InitTypesense(tsLazyLoaded *sync.Once, tsClient *typesense.Client, setupInfo TypesenseSetupInfo) {
	tsLazyLoaded.Do(func() {
		tsClient = typesense.NewClient(
			typesense.WithServer(fmt.Sprintf("https://%s:%d", setupInfo.Hosts[0], setupInfo.Port)),
			typesense.WithAPIKey(setupInfo.APIKey),
			typesense.WithConnectionTimeout(time.Duration(setupInfo.TimeoutSeconds)*time.Second))
	})
}
