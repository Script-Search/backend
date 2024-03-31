package function

import (
	"fmt"
	"sync"
	"time"

	"github.com/typesense/typesense-go/typesense"
)

var (
	TypesenseClient     *typesense.Client
	typesenseLazyLoaded sync.Once
)

func InitTypesense() {
	typesenseLazyLoaded.Do(func() {
		TypesenseClient = typesense.NewClient(
			typesense.WithServer(fmt.Sprintf("http://%s:%d", TypesenseHosts[0], TypesensePort)),
			typesense.WithAPIKey(TypesenseAPIKey),
			typesense.WithConnectionTimeout(5*time.Second))
	})
}
