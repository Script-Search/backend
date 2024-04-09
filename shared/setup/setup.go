package setup

import (
	"os"
)

type PubSubSetupInfo struct {
	ProjectId       string
	TopicName       string
	CredentialsFile string
}

func FixDir() {
	gcloudFuncSourceDir := "serverless_function_source_code"
	fileInfo, err := os.Stat(gcloudFuncSourceDir)
	if err == nil && fileInfo.IsDir() {
		_ = os.Chdir(gcloudFuncSourceDir)
	}
}
