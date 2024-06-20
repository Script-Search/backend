package function

import "time"

type TranscriptDoc struct {
	ChannelId   string    `json:"channel_id"`
	ChannelName string    `json:"channel_name"`
	VideoId     string    `json:"video_id"`
	Duration    int       `json:"duration"`
	Title       string    `json:"title"`
	UploadDate  int       `json:"upload_date"`
	TTL         time.Time `json:"ttl"`
}

type MessagePublishedData struct {
	Message PubSubMessage
}

type PubSubMessage struct {
	Data []byte `json:"data"`
}
