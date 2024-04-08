package function

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"strings"
	"time"

	
	"cloud.google.com/go/pubsub"
	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
)

type MessagePublishedData struct {
	Message PubSubMessage
}

type PubSubMessage struct {
	Data []byte `json:"data"`
}

func init() {
	FixDir()
	functions.CloudEvent("PubMissingIds", pubMissingIds)
}

func pubMissingIds(ctx context.Context, e event.Event) error {
	InitFirestore(ctx)
	InitPubSub(ctx)

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

func pubMissingVideoUrl(ctx context.Context, videoIds []string) error {
	req := CreateBatchGetRequest(videoIds)
	t := time.Now()
	stream, err := firestoreClient.BatchGetDocuments(ctx, req)
	if err != nil {
		return fmt.Errorf("batch get documents error: %v", err)
	}
	log.Printf("batch get took %s", time.Since(t))
	defer stream.CloseSend()

	t = time.Now()
	var results []*pubsub.PublishResult
	batchVideoIds := make([]string, 0, ID_BATCH_SIZE) // size 0, capacity batch_size
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
			batchVideoIds = append(batchVideoIds, missingPath[lastSlashIndex+1:])
		}

		if len(batchVideoIds) == ID_BATCH_SIZE {
			TryBatchPubSub(ctx, &batchVideoIds, &results)
		}
	}
	if len(batchVideoIds) > 0 {
		TryBatchPubSub(ctx, &batchVideoIds, &results)
	}

	// process all the results
	err = processPubSubResults(ctx, results)
	if err != nil {
		return fmt.Errorf("error processing results: %v", err)
	}
	log.Printf("processing stream took %s", time.Since(t))
	return nil
}

func processPubSubResults(ctx context.Context, results []*pubsub.PublishResult) error {
	for _, r := range results {
		_, err := r.Get(ctx)
		if err != nil {
			return fmt.Errorf("pubsub processing error: %s", err)
		}
	}
	return nil
}
