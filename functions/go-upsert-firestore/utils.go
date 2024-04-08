package function

import (
	"fmt"

	firestorepb "cloud.google.com/go/firestore/apiv1/firestorepb"
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

func mapDocumentsToWrites(videoDocs []TranscriptDoc) []*firestorepb.Write {
	writes := make([]*firestorepb.Write, len(videoDocs))
	for i, videoDoc := range videoDocs {
		writes[i] = &firestorepb.Write{
			Operation: &firestorepb.Write_Update{
				Update: docToFirestore(videoDoc),
			},
		}
	}
	return writes
}

func docToFirestore(doc TranscriptDoc) *firestorepb.Document {
	return &firestorepb.Document{
		Name: fmt.Sprintf("%s/documents/%s/%s", DatabaseUrl, documentPath, doc.VideoId),
		Fields: map[string]*firestorepb.Value{
			"channel_id":   {ValueType: &firestorepb.Value_StringValue{StringValue: doc.ChannelId}},
			"channel_name": {ValueType: &firestorepb.Value_StringValue{StringValue: doc.ChannelName}},
			"video_id":     {ValueType: &firestorepb.Value_StringValue{StringValue: doc.VideoId}},
			"duration":     {ValueType: &firestorepb.Value_IntegerValue{IntegerValue: int64(doc.Duration)}},
			"title":        {ValueType: &firestorepb.Value_StringValue{StringValue: doc.Title}},
			"upload_date":  {ValueType: &firestorepb.Value_IntegerValue{IntegerValue: int64(doc.UploadDate)}},
		},
	}
}
