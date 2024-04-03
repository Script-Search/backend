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

type TranscriptDoc struct {
	ChannelId   string   `json:"channel_id"`
	ChannelName string   `json:"channel_name"`
	VideoId     string   `json:"video_id"`
	Duration    int      `json:"duration"`
	Title       string   `json:"title"`
	UploadDate  int      `json:"upload_date"`
	Transcript  []string `json:"transcript"`
	Timestamps  []int    `json:"timestamps"`
}

type MessagePublishedData struct {
	Message PubSubMessage
}

type PubSubMessage struct {
	Data []byte `json:"data"`
}

func init() {
	FixDir()
	functions.CloudEvent("UpsertToFirestore", upsertToFirestore)
}

func upsertToFirestore(ctx context.Context, e event.Event) error {
	InitFirestore(ctx)

	// Process the msg and convert to golang slice of strings
	var msg MessagePublishedData
	if err := e.DataAs(&msg); err != nil {
		return fmt.Errorf("event.DataAs: %v", err)
	}

	jsonString := string(msg.Message.Data) // Automatically decoded from base64
	var videoDocs []TranscriptDoc
	if err := json.Unmarshal([]byte(jsonString), &videoDocs); err != nil {
		return fmt.Errorf("json unmarshal error: %v", err)
	}

	log.Printf("batch write size: %d\n", len(videoDocs))
	batchWriteVideoDocs(ctx, videoDocs)
	return nil
}

func batchWriteVideoDocs(ctx context.Context, videoDocs []TranscriptDoc) {
	t := time.Now()
	resp, err := FirestoreClient.BatchWrite(ctx, CreateBatchWriteRequest(videoDocs))
	if err != nil {
		log.Fatalln("Error occured in batch write:", err)
	}
	log.Printf("batch write took %s\n", time.Since(t))
	log.Printf("batch writes ok statuses: %d/%d\n", GetValidWriteStatuses(resp), len(videoDocs))
}
