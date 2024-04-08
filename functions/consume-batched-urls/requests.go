package function

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"io"
	"net/http"
	"time"
)

var (
	httpClient         http.Client
	YT_PLAYER_ENDPOINT = "https://youtubei.googleapis.com/youtubei/v1/player?key=AIzaSyDCU8hByM-4DrUqRUYnGn-3llEO78bcxq8"
)

func init() {
	httpClient = http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        200,
			MaxIdleConnsPerHost: 200,
			IdleConnTimeout:     10 * time.Second,
		},
		Timeout: time.Duration(1) * time.Second,
	}
}

func SendPlayerReq(ctx context.Context, yid string, client string) (*TmpPlayerResponse, error) {
	var (
		req *http.Request
		err error
	)
	if client == "web" {
		req, err = createWebReqData(yid)
	} else if client == "embedded" {
		req, err = createEmbeddedReqData(yid)
	} else {
		return nil, fmt.Errorf("err unexpected client: %s", client)
	}
	if err != nil {
		return nil, fmt.Errorf("err creating new req: %s", err)
	}
	webPlayerResp, err := httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("err sending player req: %s", err)
	}
	defer webPlayerResp.Body.Close()

	var reader io.Reader = webPlayerResp.Body
	// Check if the content is gzip-encoded
	if webPlayerResp.Header.Get("Content-Encoding") == "gzip" {
		gzipReader, err := gzip.NewReader(webPlayerResp.Body)
		if err != nil {
			return nil, fmt.Errorf("err creating gzip reader: %s", err)
		}
		defer gzipReader.Close()
		reader = gzipReader
	}

	// Read the response
	tmpPlayerResponse := &TmpPlayerResponse{}
	err = json.NewDecoder(reader).Decode(tmpPlayerResponse)
	if err != nil {
		return nil, fmt.Errorf("err reading pr body: %s", err)
	}
	return tmpPlayerResponse, nil
}

func SendTimedTextReq(ctx context.Context, tPR *TmpPlayerResponse, yid string) ([]string, []int, error) {
	timedTextUrl := GetTimedTextUrl(tPR)
	if timedTextUrl == "" {
		return nil, nil, fmt.Errorf("err no en subtitles for %s", yid)
	}
	req, err := createTTMLReqData(timedTextUrl + "&fmt=ttml")
	if err != nil {
		return nil, nil, err
	}
	timedTextResp, err := httpClient.Do(req)
	if err != nil {
		return nil, nil, err
	}
	defer timedTextResp.Body.Close()

	transcript := &Transcript{}
	err = xml.NewDecoder(timedTextResp.Body).Decode(transcript)
	if err != nil {
		return nil, nil, err
	}

	timestampsSec := make([]int, len(transcript.Body.Div.TimeStamps))
	subtitles := make([]string, len(transcript.Body.Div.TimeStamps))

	for i, timestamp := range transcript.Body.Div.TimeStamps {
		subtitles[i] = timestamp.Text
		timestampsSec[i] = convertTimestampToSeconds(timestamp.Begin)
	}

	return subtitles, timestampsSec, nil
}

func createWebReqData(yid string) (*http.Request, error) {
	// Make a post request and get the stream of the response
	postBody, _ := json.Marshal(map[string]interface{}{
		"videoId": yid,
		"context": map[string]interface{}{
			"client": map[string]interface{}{
				"clientName":    "WEB",
				"clientVersion": "2.20220801.00.00",
			},
		},
		"playbackContext": map[string]interface{}{
			"contentPlaybackContext": map[string]interface{}{
				"html5Preference": "HTML5_PREF_WANTS",
			},
		},
		"contentCheckOk": true,
		"racyCheckOk":    true,
	})
	responseBody := bytes.NewBuffer(postBody)
	req, err := http.NewRequest("POST", YT_PLAYER_ENDPOINT, responseBody)
	if err != nil {
		return nil, err
	}
	req.Header.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")
	req.Header.Add("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("X-Youtube-Client-Name", "1")
	req.Header.Add("X-Youtube-Client-Version", "2.20220801.00.00")
	req.Header.Add("Origin", "https://www.youtube.com")
	req.Header.Add("Accept-Encoding", "gzip, deflate")
	return req, nil
}

func createEmbeddedReqData(yid string) (*http.Request, error) {
	// Make a post request and get the stream of the response
	postBody, _ := json.Marshal(map[string]interface{}{
		"videoId": yid,
		"context": map[string]interface{}{
			"client": map[string]interface{}{
				"clientName":    "TVHTML5_SIMPLY_EMBEDDED_PLAYER",
				"clientVersion": "2.0",
			},
		},
		"playbackContext": map[string]interface{}{
			"contentPlaybackContext": map[string]interface{}{
				"html5Preference": "HTML5_PREF_WANTS",
			},
		},
		"contentCheckOk": true,
		"racyCheckOk":    true,
	})
	responseBody := bytes.NewBuffer(postBody)
	req, err := http.NewRequest("POST", YT_PLAYER_ENDPOINT, responseBody)
	if err != nil {
		return nil, err
	}
	req.Header.Add("User-Agent", "Mozilla/5.0 (PlayStation 4 5.55) AppleWebKit/601.2 (KHTML, like Gecko)")
	req.Header.Add("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8")
	req.Header.Add("Content-Type", "application/json")
	req.Header.Add("X-Youtube-Client-Name", "85")
	req.Header.Add("X-Youtube-Client-Version", "2.0")
	req.Header.Add("Origin", "https://www.youtube.com")
	req.Header.Add("Accept-Encoding", "gzip, deflate")
	return req, nil
}

func createTTMLReqData(url string) (*http.Request, error) {
	req, err := http.NewRequest("GET", url, nil)
	if err != nil {
		return nil, err
	}
	req.Header.Add("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36")
	req.Header.Add("Accept", "*/*")
	req.Header.Add("Content-Type", "text/xml; charset=UTF-8")
	return req, nil
}
