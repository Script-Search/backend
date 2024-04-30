package function

import (
	"encoding/json"
	"sync"
	"testing"
)

func logError(errCh chan string, t *testing.T) {
	if len(errCh) > 0 {
		errorResponses := make([]string, len(errCh))
		j := 0
		for err := range errCh {
			errorResponses[j] = err
			j++
		}
		t.Error("Invalid PR's: ", errorResponses)
	}
}

// Unit testing intermidary functions
func TestTimestampConversion(t *testing.T) {
	timestamp := "01:01:01.680"
	seconds := convertTimestampToSeconds(timestamp)
	if seconds != 3661 {
		t.Errorf("Expected 3661, got %d instead", seconds)
	}
}

func TestParseUploadDate(t *testing.T) {
	uploadDate := "2024-01-18T00:09:48-08:00"
	intUploadDate := ParseUploadDate(uploadDate)
	if intUploadDate != 20240118 {
		t.Errorf("Expected 20240118, got %d instead", intUploadDate)
	}
}

func TestIsAgeGated(t *testing.T) {
	tests := []struct {
		name     string
		response TmpPlayerResponse
		want     bool
	}{
		{
			name: "Age Verification Required Status",
			response: TmpPlayerResponse{
				PlayableStatus: struct {
					Status string "json:\"status\""
					Reason string "json:\"reason\""
				}{
					Status: "age_verification_required",
					Reason: "Please confirm your age to proceed.",
				},
			},
			want: true,
		},
		{
			name: "No Age Gate with Generic Status",
			response: TmpPlayerResponse{
				PlayableStatus: struct {
					Status string "json:\"status\""
					Reason string "json:\"reason\""
				}{
					Status: "available",
					Reason: "Content is available for all users.",
				},
			},
			want: false,
		},
		{
			name: "Age Gate by Reason",
			response: TmpPlayerResponse{
				PlayableStatus: struct {
					Status string "json:\"status\""
					Reason string "json:\"reason\""
				}{
					Status: "not_playable",
					Reason: "age-restricted",
				},
			},
			want: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := IsAgeGated(&tt.response); got != tt.want {
				t.Errorf("IsAgeGated() = %v, want %v", got, tt.want)
			}
		})
	}
}

func TestGetTimedTextUrl(t *testing.T) {
	tests := []struct {
		name     string
		jsonData string
		want     string
	}{
		{
			name: "Exact Match VSS ID",
			jsonData: `{
				"captions": {
					"playerCaptionsTracklistRenderer": {
						"captionTracks": [
							{
								"baseUrl": "http://example.com/caption.en",
								"vssId": ".en"
							}
						]
					}
				}
			}`,
			want: "http://example.com/caption.en",
		},
		{
			name: "Fallback to Contains .en",
			jsonData: `{
				"captions": {
					"playerCaptionsTracklistRenderer": {
						"captionTracks": [
							{
								"baseUrl": "http://example.com/caption.en.us",
								"vssId": "a.en"
							},
							{
								"baseUrl": "http://example.com/caption.en",
								"vssId": "b.en"
							}
						]
					}
				}
			}`,
			want: "http://example.com/caption.en",
		},
		{
			name: "Default to a.en",
			jsonData: `{
				"captions": {
					"playerCaptionsTracklistRenderer": {
						"captionTracks": [
							{
								"baseUrl": "http://example.com/caption.en.us",
								"vssId": "a.en"
							}
						]
					}
				}
			}`,
			want: "http://example.com/caption.en.us",
		},
		{
			name: "No English Captions",
			jsonData: `{
				"captions": {
					"playerCaptionsTracklistRenderer": {
						"captionTracks": [
							{
								"baseUrl": "http://example.com/caption.es",
								"vssId": "a.es"
							}
						]
					}
				}
			}`,
			want: "",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			var response TmpPlayerResponse
			if err := json.Unmarshal([]byte(tt.jsonData), &response); err != nil {
				t.Fatalf("Failed to unmarshal JSON: %v", err)
			}

			if got := GetTimedTextUrl(&response); got != tt.want {
				t.Errorf("GetTimedTextUrl() = %v, want %v", got, tt.want)
			}
		})
	}
}

// Everything below functions as integration tests
func TestSendWeb(t *testing.T) {
	videoIds := []string{"_uQgGS_VIXM"}
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

	logError(errCh, t)
}

func TestSendEmbedded(t *testing.T) {
	videoIds := []string{"KJTw5xXxyKk"}
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

	logError(errCh, t)
}

func TestBatchedSend(t *testing.T) {
	videoIds := []string{
		"2V7yPrxJ8Ck", "UrcwDOEBzZE", "a3Aep-SygUA", "QHXET1G9Y5U", "JtdB-jiN6O0",
		"l8dpetPPkFQ", "6pzoo2HXJT8", "8wysIxzqgPI", "3A_YMWcx4HI", "i53Gi_K3o7I",
		"hL0bn_-FKmo", "tAuRQs_d9F8", "SpOCDsxouJ4", "jgQjes7MgTM", "D9IFZnIhoe4",
		"jPKTo1iGQiE", "dncBmGtYJ9g", "o5n85GRKuzk", "46dZH7LDbf8", "Hmf7a5u8nCk",
		"akXP6pC0piE", "BgLTDT03QtU", "0K_eZGS5NsU", "qMky6D6YtXU", "_i4Yxeh5ceQ",
	}
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

	logError(errCh, t)
}
