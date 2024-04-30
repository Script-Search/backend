package function

import (
	"context"
	"testing"
	"time"
)

func init() {
	InitFirestore(context.Background())
}

func cleanup(ctx context.Context, videoDocs []TranscriptDoc) {
	for _, doc := range videoDocs {
		FirestoreClient.DeleteDocument(ctx, CreateDelRequest(doc))
	}
}

func TestBatchUpsert(t *testing.T) {
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	singleDoc := []TranscriptDoc{
		{
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

	multipleDocs := []TranscriptDoc{
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid01",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid02",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid03",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid04",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid05",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid06",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid07",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid08",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
			ChannelId:   "testCh1",
			ChannelName: "testCh",
			VideoId:     "testVid09",
			Duration:    10,
			Title:       "testTitle",
			UploadDate:  20240409,
			Transcript:  []string{"hi", "bye"},
			Timestamps:  []int{2, 5},
		},
		{
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
		err := batchWriteVideoDocs(ctx, singleDoc)
		if err != nil {
			t.Error("error in batchUpsert:", err)
		}
		cleanup(ctx, singleDoc)
	})

	t.Run("Multiple", func(t *testing.T) {
		err := batchWriteVideoDocs(ctx, multipleDocs)
		if err != nil {
			t.Error("error in batchUpsert:", err)
		}
		cleanup(ctx, multipleDocs)
	})
}
