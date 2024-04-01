package function

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
	"github.com/typesense/typesense-go/typesense/api"
	"github.com/typesense/typesense-go/typesense/api/pointer"
)

type TranscriptDoc struct {
	Id          string   `json:"id"`
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
	InitConfig()
	InitTypesense()
	functions.CloudEvent("UpsertToTypesense", upsertToTypesense)
}

func upsertToTypesense(ctx context.Context, e event.Event) error {
	// Process the msg and convert to golang slice of strings
	var msg MessagePublishedData
	if err := e.DataAs(&msg); err != nil {
		return fmt.Errorf("event.DataAs: %v", err)
	}

	jsonString := string(msg.Message.Data) // Automatically decoded from base64
	var videoDocs []TranscriptDoc
	if err := json.Unmarshal([]byte(jsonString), &videoDocs); err != nil {
		return fmt.Errorf("json unmarshal error: %s", err.Error())
	}

	// Need to convert it to this in order for it to be valid function input
	var documents []interface{} = make([]interface{}, len(videoDocs))
	for i, doc := range videoDocs {
		documents[i] = doc
	}

	fmt.Printf("batch write size: %d\n", len(videoDocs))

	t := time.Now()
	params := &api.ImportDocumentsParams{
		Action: pointer.String("upsert"),
		BatchSize: pointer.Int(len(documents)),
	}
	_, err := TypesenseClient.Collection(TypesenseCollectionName).Documents().Import(ctx, documents, params)
	if err != nil {
		return fmt.Errorf("batch upsert error: %s", err.Error())
	}
	fmt.Printf("bulk import took %s\n", time.Since(t))
	return nil
}
