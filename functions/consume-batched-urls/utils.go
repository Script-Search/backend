package function

import (
	"fmt"
	"reflect"
	"strconv"
	"strings"
)

var (
	AgeGateReasons = []string{
		"confirm your age", "age-restricted", "inappropriate", // reason
		"age_verification_required", "age_check_required", // status
	}
)

func GetTimedTextUrl(tPR *TmpPlayerResponse) string {
	var subtitleUrl string
	for _, captionTrack := range tPR.Captions.TracklistRenderer.CaptionTracks {
		switch {
		case captionTrack.VssId == ".en":
			return captionTrack.BaseUrl
		case strings.Contains(captionTrack.VssId, ".en"):
			subtitleUrl = captionTrack.BaseUrl
		case captionTrack.VssId == "a.en" && subtitleUrl == "":
			subtitleUrl = captionTrack.BaseUrl
		}
	}
	return subtitleUrl
}

func IsAgeGated(tPR *TmpPlayerResponse) bool {
	statuses := []string{tPR.PlayableStatus.Reason, tPR.PlayableStatus.Status}
	for _, status := range statuses {
		for _, ageGateReason := range AgeGateReasons {
			if strings.Contains(status, ageGateReason) {
				return true
			}
		}
	}
	return false
}

func ParseUploadDate(uploadDate string) int {
	if uploadDate == "" {
		return -1 // undefiend
	}
	parts := strings.Split(uploadDate, "-")
	year := parts[0]
	month := parts[1]
	day := parts[2][:2]

	uploadDateInt, _ := strconv.Atoi(fmt.Sprintf("%s%s%s", year, month, day))
	return uploadDateInt
}

func convertTimestampToSeconds(timestamp string) int {
	if timestamp == "" {
		return -1 // undefined
	}
	parts := strings.Split(timestamp, ":")
	hours, _ := strconv.Atoi(parts[0])
	minutes, _ := strconv.Atoi(parts[1])
	secondsPart := strings.Split(parts[2], ".")
	seconds, _ := strconv.Atoi(secondsPart[0])
	return hours*3600 + minutes*60 + seconds
}

func ValidateStruct(s interface{}) (err error) {
	// now go one by one through the fields and validate their value
	structType := reflect.TypeOf(s)
	structVal := reflect.ValueOf(s)
	fieldNum := structVal.NumField()

	for i := 0; i < fieldNum; i++ {
		// Field(i) returns i'th value of the struct
		field := structVal.Field(i)
		fieldName := structType.Field(i).Name

		isSet := field.IsValid() && !field.IsZero()

		if !isSet {
			return fmt.Errorf("%s is not set", fieldName)
		}
	}
	return err
}
