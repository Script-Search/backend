package function

import (
	"encoding/xml"
	"io"
	"strings"
)

type Transcript struct {
	Body struct {
		Div struct {
			TimeStamps []TimeStamp `xml:"p"`
		} `xml:"div"`
	} `xml:"body"`
}

type TimeStamp struct {
	Begin string `xml:"begin,attr"`
	Text  string `xml:",chardata"`
}

// Custom unmarshaler for TimeStamp to handle <br> tags properly
func (ts *TimeStamp) UnmarshalXML(d *xml.Decoder, start xml.StartElement) error {
	var result strings.Builder
	for {
		token, err := d.Token()
		if err == io.EOF {
			break
		}
		if err != nil {
			return err
		}

		switch t := token.(type) {
		case xml.CharData:
			result.Write(t)
		case xml.StartElement:
			if t.Name.Local == "br" {
				result.WriteRune(' ')
				// Skip the <br> element itself
				d.Skip()
			}
		}
	}

	ts.Text = result.String()
	for _, attr := range start.Attr {
		if attr.Name.Local == "begin" {
			ts.Begin = attr.Value
			break
		}
	}
	return nil
}

type PlayerResponse struct {
	Id          string   `json:"id"`
	ChannelId   string   `json:"channel_id"`
	ChannelName string   `json:"channel_name"`
	VideoId     string   `json:"video_id"`
	Duration    int      `json:"duration"`
	Title       string   `json:"title"`
	UploadDate  int      `json:"upload_date"`
	Transcript  []string `json:"transcript"`
	Timestamps  []int    `json:"timestamps"`
}

type TmpPlayerResponse struct {
	PlayableStatus struct {
		Status string `json:"status"`
		Reason string `json:"reason"`
	} `json:"playabilityStatus"`
	VideoDetails struct {
		VideoId   string `json:"videoId"`
		Title     string `json:"title"`
		Duration  string `json:"lengthSeconds"`
		ChannelId string `json:"channelId"`
		Channel   string `json:"author"`
	} `json:"videoDetails"`
	Microformat struct {
		PlayerMicroformatRenderer struct {
			UploadDate string `json:"uploadDate"`
		} `json:"playerMicroformatRenderer"`
	} `json:"microformat"`
	Captions struct {
		TracklistRenderer struct {
			CaptionTracks []struct {
				BaseUrl      string `json:"baseUrl"`
				LanguageCode string `json:"languageCode"`
				VssId        string `json:"vssId"`
			} `json:"captionTracks"`
		} `json:"playerCaptionsTracklistRenderer"`
	} `json:"captions"`
}

type MessagePublishedData struct {
	Message PubSubMessage
}

type PubSubMessage struct {
	Data []byte `json:"data"`
}
