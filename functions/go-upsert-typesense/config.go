package function

import (
	"log"
	"os"
	"strconv"
	"strings"

	"github.com/joho/godotenv"
)

var FirestoreCollectionPath string
var FirestoreCollectionFields []string
var ShouldFlattenNestedDocuments bool
var TypesenseHosts []string
var TypesensePort int
var TypesenseProtocol string
var TypesenseCollectionName string
var TypesenseAPIKey string
var TypesenseBackfillTriggerDocumentInFirestore string = "typesense_sync/backfill"
var TypesenseBackfillBatchSize int = 1000

func InitConfig() {
	err := godotenv.Load(".env")
	if err != nil {
		log.Fatalf("Error loading .env file: %s", err)
	}

	FirestoreCollectionPath = os.Getenv("FIRESTORE_COLLECTION_PATH")
	FirestoreCollectionFields = filterAndTrim(strings.Split(os.Getenv("FIRESTORE_COLLECTION_FIELDS"), ","))
	ShouldFlattenNestedDocuments = os.Getenv("FLATTEN_NESTED_DOCUMENTS") == "true"
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
