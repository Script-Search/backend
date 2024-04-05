package function

import (
	"context"
	"encoding/json"
	"sync"

	"fmt"
	"log"
	"strconv"

	"time"

	"cloud.google.com/go/pubsub"
	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
)

func init() {
	FixDir()
	functions.CloudEvent("ConsumeBatchedUrls", consumeBatchedUrls)
}

// Should take a url, Client (clientname, version, headers)
func send(ctx context.Context, yid string, ch chan *PlayerResponse, wg *sync.WaitGroup) {
	defer wg.Done()
	startTime := time.Now()

	tmpPlayerResponse, err := SendPlayerReq(ctx, yid, "web")
	if err != nil {
		fmt.Println(err)
		return
	}

	// TODO: Add retry (up to 3 perhaps)
	uploadDate := ParseUploadDate(tmpPlayerResponse.Microformat.PlayerMicroformatRenderer.UploadDate)

	if IsAgeGated(tmpPlayerResponse) {
		tmpPlayerResponse, err = SendPlayerReq(ctx, yid, "embedded")
		if err != nil {
			fmt.Println(err)
			return
		}
	}

	// Verify that we're not IP blocked (unlikely)
	if yid != tmpPlayerResponse.VideoDetails.VideoId {
		fmt.Println("error in sending request, received response with different videoId")
		return
	}

	subtitles, timestamps, err := SendTimedTextReq(ctx, tmpPlayerResponse, yid)
	if err != nil {
		fmt.Printf("error occurred getting timed text ttml for %s\n", yid)
		return
	}

	vidDuration, _ := strconv.Atoi(tmpPlayerResponse.VideoDetails.Duration)

	playerResponse := &PlayerResponse{
		Id:          yid,
		VideoId:     yid,
		Title:       tmpPlayerResponse.VideoDetails.Title,
		Duration:    vidDuration,
		ChannelId:   tmpPlayerResponse.VideoDetails.ChannelId,
		ChannelName: tmpPlayerResponse.VideoDetails.Channel,
		UploadDate:  uploadDate,
		Transcript:  subtitles,
		Timestamps:  timestamps,
	}

	// Verify all fields populated
	err = ValidateStruct(*playerResponse)
	if err != nil {
		fmt.Printf("error in player response: %s", err)
		return
	}

	fmt.Printf("sending %s took %s\n", yid, time.Since(startTime))
	ch <- playerResponse
}

func consumeBatchedUrls(ctx context.Context, e event.Event) error {
	InitPubSub(ctx)

	// Process the msg and convert to golang slice of strings
	var msg MessagePublishedData
	if err := e.DataAs(&msg); err != nil {
		return fmt.Errorf("event.DataAs: %v", err)
	}

	jsonString := string(msg.Message.Data) // Automatically decoded from base64
	var videoIds []string
	if err := json.Unmarshal([]byte(jsonString), &videoIds); err != nil {
		return fmt.Errorf("json unmarshal error: %v", err)
	}

	t := time.Now()
	var wg sync.WaitGroup

	ch := make(chan *PlayerResponse, len(videoIds))

	for _, videoId := range videoIds {
		wg.Add(1)
		go send(ctx, videoId, ch, &wg)
	}

	wg.Wait()
	close(ch)

	playerResponses := make([]*PlayerResponse, len(ch))
	i := 0
	for pr := range ch {
		playerResponses[i] = pr
		i++
	}

	// Send the batch request using responses from chTT
	if len(playerResponses) > 0 {
		prJson, _ := json.Marshal(playerResponses)
		result := topic.Publish(ctx, &pubsub.Message{
			Data: []byte(prJson),
		})
		result.Get(ctx)
	}

	log.Printf("handler took %s", time.Since(t))
	return nil
}
