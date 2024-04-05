package function

type Transcript struct {
	Body struct {
		Div struct {
			TimeStamps []struct {
				Begin string `xml:"begin,attr"`
				Text  string `xml:",chardata"`
			} `xml:"p"`
		} `xml:"div"`
	} `xml:"body"`
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
