package function

import (
	"fmt"
	"sync"

	"github.com/typesense/typesense-go/typesense"
)

var (
	TypesenseClient     *typesense.Client
	typesenseLazyLoaded sync.Once
)

func init() {
	typesenseLazyLoaded.Do(func() {
		TypesenseClient = typesense.NewClient(
			typesense.WithServer(fmt.Sprintf("%s:%d", TypesenseHosts[0], TypesensePort)),
			typesense.WithAPIKey(TypesenseAPIKey),
			typesense.WithConnectionTimeout(60))
	})
}
