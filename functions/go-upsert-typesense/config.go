package function

import (
	"fmt"
	"log"
	"os"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/joho/godotenv"
	"github.com/typesense/typesense-go/typesense"
)

var (
	TypesenseHosts             []string
	TypesensePort              int
	TypesenseProtocol          string
	TypesenseCollectionName    string
	TypesenseAPIKey            string
	TypesenseBackfillBatchSize int = 1000

	TypesenseClient     *typesense.Client
	typesenseLazyLoaded sync.Once
)

func InitTypesense(tsLazyLoaded *sync.Once) {
	tsLazyLoaded.Do(func() {
		TypesenseClient = typesense.NewClient(
			typesense.WithServer(fmt.Sprintf("https://%s:%d", TypesenseHosts[0], TypesensePort)),
			typesense.WithAPIKey(TypesenseAPIKey),
			typesense.WithConnectionTimeout(5*time.Second))
	})
}

func InitConfig() {
	err := godotenv.Load(".env")
	if err != nil {
		log.Fatalf("Error loading .env file: %s", err)
	}

	TypesenseHosts = filterAndTrim(strings.Split(os.Getenv("TYPESENSE_HOSTS"), ","))
	TypesensePort, _ = strconv.Atoi(os.Getenv("TYPESENSE_PORT"))
	if TypesensePort == 0 {
		TypesensePort = 443 // default value if not set
	}
	TypesenseProtocol = os.Getenv("TYPESENSE_PROTOCOL")
	if TypesenseProtocol == "" {
		TypesenseProtocol = "https" // default value if not set
	}
	TypesenseCollectionName = os.Getenv("TYPESENSE_COLLECTION_NAME")
	TypesenseAPIKey = os.Getenv("TYPESENSE_API_KEY")
}

func filterAndTrim(arr []string) []string {
	var result []string
	for _, item := range arr {
		trimmedItem := strings.TrimSpace(item)
		if trimmedItem != "" {
			result = append(result, trimmedItem)
		}
	}
	return result
}

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}
