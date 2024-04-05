package function

import (
	"context"
	"encoding/json"
	"fmt"

	firestorepb "cloud.google.com/go/firestore/apiv1/firestorepb"
	"cloud.google.com/go/pubsub"
)

func TryBatchPubSub(ctx context.Context, batchVideoIds *[]string, results *[]*pubsub.PublishResult) {
	ids, _ := json.Marshal(batchVideoIds)
	result := topic.Publish(ctx, &pubsub.Message{
		Data: []byte(ids),
	})
	*results = append(*results, result)
	*batchVideoIds = (*batchVideoIds)[:0] // Keep the capacity, rem size
}

func CreateBatchGetRequest(videoIds []string) *firestorepb.BatchGetDocumentsRequest {
	return &firestorepb.BatchGetDocumentsRequest{
		Database:  databaseUrl,
		Documents: mapIdsToDocuments(videoIds),
		Mask:      docMask,
	}
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
