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
	DebugAddr()
}

// Should take a url, Client (clientname, version, headers)
func send(yid string, ch chan *PlayerResponse, errCh chan string, wg *sync.WaitGroup) {
	defer wg.Done()

	tmpPlayerResponse, err := SendPlayerReq(yid, "web")
	if err != nil {
		errCh <- err.Error()
		return

	}

	if tmpPlayerResponse.Microformat.PlayerMicroformatRenderer.UploadDate == "" {
		errCh <- fmt.Sprintf("err no upload date found %s", yid)
		return
	}
	uploadDate := ParseUploadDate(tmpPlayerResponse.Microformat.PlayerMicroformatRenderer.UploadDate)

	if IsAgeGated(tmpPlayerResponse) {
		tmpPlayerResponse, err = SendPlayerReq(yid, "embedded")
		if err != nil {
			errCh <- err.Error()
			return
		}
	}

	// Verify that we're not IP blocked (unlikely)
	if yid != tmpPlayerResponse.VideoDetails.VideoId {
		errCh <- fmt.Sprintf("err response with diff videoId: %s %s", yid, tmpPlayerResponse.VideoDetails.VideoId)
		return
	}

	subtitles, timestamps, err := SendTimedTextReq(tmpPlayerResponse)
	if err != nil {
		errCh <- fmt.Sprintf("err invalid timed text ttml for %s: %s", yid, err)
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
		errCh <- fmt.Sprintf("err in pr fields: %s", err)
		return
	}

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
	errCh := make(chan string, len(videoIds))

	for _, videoId := range videoIds {
		if videoId != "" {
			wg.Add(1)
			go send(videoId, ch, errCh, &wg)
		}
	}

	wg.Wait()
	close(ch)
	close(errCh)

	playerResponses := make([]*PlayerResponse, len(ch))
	errorResponses := make([]string, len(errCh))
	i := 0
	for pr := range ch {
		playerResponses[i] = pr
		i++
	}
	j := 0
	for err := range errCh {
		errorResponses[j] = err
		j++
	}

	// Output valid urls, then errors
	log.Println("Valid PR's: ", localAddr, len(playerResponses))
	log.Println("Invalid PR's: ", localAddr, errorResponses)

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
