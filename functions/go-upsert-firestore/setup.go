package function

import (
	"context"
	"fmt"
	"log"
	"os"
	"sync"

	firestore "cloud.google.com/go/firestore/apiv1"
	"google.golang.org/api/option"
)

var (
	projectId    = os.Getenv("PROJECT_ID")
	databaseId   = os.Getenv("DATABASE_ID")
	documentPath = os.Getenv("DOCUMENT_PATH")

	// Firestore Globals
	FirestoreClient           *firestore.Client
	DatabaseUrl               = fmt.Sprintf("projects/%s/databases/%s", projectId, databaseId)
	firestoreClientLazyLoaded sync.Once // Ensure client loaded just once
)

func InitFirestore(ctx context.Context) {
	firestoreClientLazyLoaded.Do(func() {
		var err error
		sa := option.WithCredentialsFile("credentials_firebase.json")
		FirestoreClient, err = firestore.NewClient(ctx, sa)
		if err != nil {
			log.Fatalln(err)
		}
	})
}

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}
