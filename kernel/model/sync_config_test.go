// SiYuan - https://github.com/siyuan-note/siyuan
// Copyright (c) 2020-present, b3log.org
// SPDX-License-Identifier: AGPL-3.0-or-later

package model

import (
	"testing"

	"github.com/siyuan-note/siyuan/kernel/conf"
)

func TestCheckSyncPreservesEnabledWithoutUser(t *testing.T) {
	originalConf := Conf
	Conf = NewAppConf()
	Conf.Sync.Store(conf.NewSync())
	Conf.Sync.Load().Enabled = true
	t.Cleanup(func() {
		Conf = originalConf
	})

	if checkSync(false, false, true) {
		t.Fatal("sync must not start without a user")
	}
	if !Conf.Sync.Load().Enabled {
		t.Fatal("sync configuration must remain enabled without a user")
	}
}

func TestSelfHostedSyncWithoutSiYuanAccount(t *testing.T) {
	originalConf := Conf
	t.Cleanup(func() { Conf = originalConf })
	for _, provider := range []int{conf.ProviderS3, conf.ProviderWebDAV, conf.ProviderLocal} {
		Conf = NewAppConf()
		Conf.Sync.Store(conf.NewSync())
		Conf.Sync.Load().Provider = provider
		Conf.Sync.Load().Enabled = true
		if !checkSync(false, false, true) {
			t.Fatalf("self-hosted provider %d requires an account", provider)
		}
		if err := checkAssetDownloadAccess(); err != nil {
			t.Fatalf("self-hosted provider %d cannot download assets: %v", provider, err)
		}
		Conf.Sync.Load().Enabled = false
		if checkAssetDownloadAccess() == nil {
			t.Fatalf("disabled provider %d can download assets", provider)
		}
	}
	Conf.Sync.Load().Provider = conf.ProviderSiYuan
	Conf.Sync.Load().Enabled = true
	if checkSync(false, false, true) || checkAssetDownloadAccess() == nil {
		t.Fatal("official cloud must still require a subscription")
	}
	Conf.Sync.Load().Provider = -1
	if checkSync(false, false, true) || checkAssetDownloadAccess() == nil {
		t.Fatal("unknown providers must be rejected")
	}
}
