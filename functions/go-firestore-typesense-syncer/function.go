package function

import (
	"context"
	"fmt"

	"github.com/GoogleCloudPlatform/functions-framework-go/functions"
	"github.com/cloudevents/sdk-go/v2/event"
	"github.com/googleapis/google-cloudevents-go/cloud/firestoredata"
	"google.golang.org/protobuf/proto"
)

func init() {
	functions.CloudEvent("IndexOnWrite", indexOnWrite)
}

func indexOnWrite(ctx context.Context, event event.Event) error {
	var data firestoredata.DocumentEventData
	if err := proto.Unmarshal(event.Data(), &data); err != nil {
		return fmt.Errorf("proto.Unmarshal: %w", err)
	}

	val := data.GetValue()

	if val == nil {
		idToDel := data.GetOldValue().Name

		fmt.Printf("Upserting document %s", idToDel)
		_, err := TypesenseClient.Collection(TypesenseCollectionName).Document(idToDel).Delete(ctx)
		if err != nil {
			return fmt.Errorf("error deleting a document (%s): %w", idToDel, err)
		}
	} else {
		var err error
		typesenseDoc, err := TypesenseDocumentFromSnapshot(val)
		if err != nil {
			return fmt.Errorf("error converting to typesense types (%s): %w", val.GetName(), err)
		}

		fmt.Printf("Upserting document %s", val.GetName())
		_, err = TypesenseClient.Collection(TypesenseCollectionName).Documents().Upsert(ctx, typesenseDoc)
		if err != nil {
			return fmt.Errorf("error upserting a document (%s): %w", typesenseDoc["id"], err)
		}
	}
	return nil
}
