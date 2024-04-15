package function

import (
	"context"
	"testing"
	"time"
)

func init() {
	InitConfig()
	InitTypesense(&typesenseLazyLoaded, TypesenseClient)
}

func cleanup() {

}

func TestBatchUpsert(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	singleDoc := []interface{}{
		TranscriptDoc{
			Id:          "test2842",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid1",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
	}

	t.Run("Single", func(t *testing.T) {
		resps, err := batchUpsert(ctx, singleDoc)
		if err != nil {
			t.Error("error in batchUpsert:", err)
		}
		defer TypesenseClient.Collection(TypesenseCollectionName).Document("test2842").Delete(ctx)

		// Check successes
		successes := 0
		for _, r := range resps {
			if r.Success {
				successes++
			}
		}

		if successes != 1 {
			t.Error("failed to batch upsert 1 doc")
		}
	})

}
