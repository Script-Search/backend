package function

import (
	"os"
	"strconv"
	"strings"
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
