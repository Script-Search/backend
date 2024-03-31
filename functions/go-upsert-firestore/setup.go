package function

import (
	"log"
	"os"
	"context"
	"sync"
	"fmt"

	firestore "cloud.google.com/go/firestore/apiv1"
	"google.golang.org/api/option"
)

var (
	projectId    = os.Getenv("PROJECT_ID")
	databaseId   = os.Getenv("DATABASE_ID")

	// Firestore Globals
	FirestoreClient           *firestore.Client
	firestoreClientLazyLoaded sync.Once // Ensure client loaded just once
	databaseUrl               = fmt.Sprintf("projects/%s/databases/%s", projectId, databaseId)
)

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}

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
