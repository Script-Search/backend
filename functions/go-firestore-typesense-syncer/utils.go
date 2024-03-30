package function

import (
	"fmt"

	"github.com/googleapis/google-cloudevents-go/cloud/firestoredata"
)

func TypesenseDocumentFromSnapshot(document *firestoredata.Document) (map[string]interface{}, error) {
	data := document.GetFields()

	// Extract fields here using config.firestoreCollectionFields; because empty, will not define for now...

	typesenseDoc := make(map[string]interface{})
	for key, item := range data {
		typesenseDoc[key] = mapValue(item)
	}

	// Flatten the document here; because empty will not define

	typesenseDoc["id"] = document.GetName()
	return typesenseDoc, nil
}

// interface{} is interchangeable with 'any'
func mapValue(value *firestoredata.Value) interface{} {

	// Typesense's official mapping function supports more types; don't consider it for now...
	switch v := value.GetValueType(); v {
	case &firestoredata.Value_ArrayValue{}:
		arr := value.GetArrayValue().GetValues()
		ret := make([]interface{}, len(arr))
		for i, item := range arr {
			ret[i] = mapValue(item)
		}
		return ret
	case &firestoredata.Value_MapValue{}:
		mp := value.GetMapValue().GetFields()
		ret := make(map[string]interface{})
		for key, item := range mp {
			ret[key] = mapValue(item)
		}
		return ret
	case &firestoredata.Value_StringValue{}:
		return value.GetStringValue()
	case &firestoredata.Value_IntegerValue{}:
		return value.GetIntegerValue()
	case &firestoredata.Value_DoubleValue{}:
		return value.GetDoubleValue()
	case &firestoredata.Value_BooleanValue{}:
		return value.GetBooleanValue()
	case &firestoredata.Value_NullValue{}:
		return nil
	default:
		// TODO: log error...
		fmt.Printf("Unexpected type encountered...")
		return value
	}
}
