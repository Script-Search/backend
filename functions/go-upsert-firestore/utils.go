package function

import (
	"fmt"
	"time"

	firestorepb "cloud.google.com/go/firestore/apiv1/firestorepb"
	"google.golang.org/protobuf/types/known/timestamppb"
)

func GetValidWriteStatuses(resp *firestorepb.BatchWriteResponse) int {
	okCnt := 0
	for _, status := range resp.GetStatus() {
		if status.GetCode() == 0 {
			// OK
			okCnt += 1
		}
	}
	return okCnt
}

func CreateBatchWriteRequest(videoDocs []TranscriptDoc) *firestorepb.BatchWriteRequest {
	return &firestorepb.BatchWriteRequest{
		Database: DatabaseUrl,
		Writes:   mapDocumentsToWrites(videoDocs),
	}
}

func CreateDelRequest(doc TranscriptDoc) *firestorepb.DeleteDocumentRequest {
	return &firestorepb.DeleteDocumentRequest{
		Name: fmt.Sprintf("%s/documents/%s/%s", DatabaseUrl, documentPath, doc.VideoId),
	}
}

func mapDocumentsToWrites(videoDocs []TranscriptDoc) []*firestorepb.Write {
	writes := make([]*firestorepb.Write, len(videoDocs))
	weekLater := time.Now().Add(7 * 24 * time.Hour)
	expiration := timestamppb.New(weekLater)
	for i, videoDoc := range videoDocs {
		writes[i] = &firestorepb.Write{
			Operation: &firestorepb.Write_Update{
				Update: docToFirestore(videoDoc, expiration),
			},
		}
	}
	return writes
}

func docToFirestore(doc TranscriptDoc, ttl *timestamppb.Timestamp) *firestorepb.Document {
	return &firestorepb.Document{
		Name: fmt.Sprintf("%s/documents/%s/%s", DatabaseUrl, documentPath, doc.VideoId),
		Fields: map[string]*firestorepb.Value{
			"channel_id":   {ValueType: &firestorepb.Value_StringValue{StringValue: doc.ChannelId}},
			"channel_name": {ValueType: &firestorepb.Value_StringValue{StringValue: doc.ChannelName}},
			"video_id":     {ValueType: &firestorepb.Value_StringValue{StringValue: doc.VideoId}},
			"duration":     {ValueType: &firestorepb.Value_IntegerValue{IntegerValue: int64(doc.Duration)}},
			"title":        {ValueType: &firestorepb.Value_StringValue{StringValue: doc.Title}},
			"upload_date":  {ValueType: &firestorepb.Value_IntegerValue{IntegerValue: int64(doc.UploadDate)}},
			"ttl":          {ValueType: &firestorepb.Value_TimestampValue{TimestampValue: ttl}},
		},
	}
}
