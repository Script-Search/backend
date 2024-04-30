package function

import (
	"context"
	"fmt"
	"testing"
	"time"
	"github.com/typesense/typesense-go/typesense/api"
	"github.com/typesense/typesense-go/typesense/api/pointer"
)

func init() {
	InitConfig()
	InitTypesense(&typesenseLazyLoaded)
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

	multipleDocs := []interface{}{
		TranscriptDoc{
			Id:          "test257",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid01",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test258",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid02",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test259",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid03",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test260",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid04",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test261",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid05",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test262",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid06",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test263",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid07",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test264",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid08",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test265",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid09",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		TranscriptDoc{
			Id:          "test266",
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid10",
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

	t.Run("Multiple", func(t *testing.T) {
		resps, err := batchUpsert(ctx, multipleDocs)
		if err != nil {
			t.Error("error in batchUpsert:", err)
		}

		fmt.Println("passed batch upsert")

		// cleanup
		filter := &api.DeleteDocumentsParams{
			FilterBy:  pointer.String("channel_name:=testCh"),
			BatchSize: pointer.Int(100),
		}
		TypesenseClient.Collection(TypesenseCollectionName).Documents().Delete(context.Background(), filter)

		// Check successes
		successes := 0
		for _, r := range resps {
			if r.Success {
				successes++
			}
		}

		if successes != 10 {
			t.Error("failed to batch upsert 10 docs")
		}
	})
}
