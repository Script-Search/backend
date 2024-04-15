package function

import (
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
	videoIds := []string{"[INSERT_EMBEDDED_ID]"}
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
