package function

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"

	firestore "cloud.google.com/go/firestore/apiv1"
	"github.com/joho/godotenv"
	"google.golang.org/api/option"
)

var (
	projectId    string
	databaseId   string
	documentPath string

	// Firestore Globals
	FirestoreClient           *firestore.Client
	DatabaseUrl               string
	firestoreClientLazyLoaded sync.Once // Ensure client loaded just once
)

func InitFirestore(ctx context.Context) {
	firestoreClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_firebase.json")
		FirestoreClient, err = firestore.NewClient(ctx, sa)
		if err != nil {
			log.Fatalf("firestore init error: %v", err)
		}
	})
}

func InitConfig() {
	err := godotenv.Load(".env")
	if err != nil {
		log.Fatalf("Error loading .env file: %s", err)
	}

	projectId = os.Getenv("PROJECT_ID")
	databaseId = os.Getenv("DATABASE_ID")
	documentPath = os.Getenv("DOCUMENT_PATH")
	DatabaseUrl = fmt.Sprintf("projects/%s/databases/%s", projectId, databaseId)
}

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}
