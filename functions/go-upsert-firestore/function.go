package function

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"time"

	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
)

func init() {
	FixDir()
	functions.CloudEvent("UpsertToFirestore", upsertToFirestore)
}

func upsertToFirestore(ctx context.Context, e event.Event) error {
	InitFirestore(ctx)

	// Process the msg and convert to golang slice of strings
	var msg MessagePublishedData
	if err := e.DataAs(&msg); err != nil {
		return fmt.Errorf("event.DataAs error: %v", err)
	}

	jsonString := string(msg.Message.Data) // Automatically decoded from base64
	var videoDocs []TranscriptDoc
	if err := json.Unmarshal([]byte(jsonString), &videoDocs); err != nil {
		return fmt.Errorf("json unmarshal error: %v", err)
	}

	return batchWriteVideoDocs(ctx, videoDocs)
}

func batchWriteVideoDocs(ctx context.Context, videoDocs []TranscriptDoc) error {
	t := time.Now()
	resp, err := FirestoreClient.BatchWrite(ctx, CreateBatchWriteRequest(videoDocs))
	if err != nil {
		return fmt.Errorf("error occured in batch write: %v", err)
	}
	log.Printf("batch write took %s\n", time.Since(t))
	log.Printf("batch writes ok statuses: %d/%d\n", GetValidWriteStatuses(resp), len(videoDocs))
	return nil
}
