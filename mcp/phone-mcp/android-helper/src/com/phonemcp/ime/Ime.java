package com.phonemcp.ime;

import android.content.BroadcastReceiver;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.inputmethodservice.InputMethodService;
import android.os.Build;
import android.util.Base64;
import android.view.inputmethod.InputConnection;

import java.nio.charset.StandardCharsets;

/**
 * Commits Unicode text and reads the clipboard for `adb shell`, which cannot do either itself.
 * Only an active input method may do these, so the server enables this one for a single
 * operation and then restores the keyboard that was in use.
 */
public final class Ime extends InputMethodService {
    private static final String TEXT = "com.phonemcp.ime.TEXT";
    private static final String CLIP_SET = "com.phonemcp.ime.CLIP_SET";
    private static final String CLIP_GET = "com.phonemcp.ime.CLIP_GET";
    private static final int OK = 1;
    private static final int NO_FIELD = 2;

    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        @Override
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (TEXT.equals(action)) {
                InputConnection ic = getCurrentInputConnection();
                if (ic == null) {
                    setResultCode(NO_FIELD);
                    return;
                }
                ic.commitText(decode(intent), 1);
                setResultCode(OK);
            } else if (CLIP_SET.equals(action)) {
                clipboard().setPrimaryClip(ClipData.newPlainText("phone-mcp", decode(intent)));
                setResultCode(OK);
            } else if (CLIP_GET.equals(action)) {
                ClipData clip = clipboard().getPrimaryClip();
                CharSequence text = clip != null && clip.getItemCount() > 0
                        ? clip.getItemAt(0).coerceToText(Ime.this) : "";
                setResultData(Base64.encodeToString(
                        text.toString().getBytes(StandardCharsets.UTF_8), Base64.NO_WRAP));
                setResultCode(OK);
            }
        }
    };

    private ClipboardManager clipboard() {
        return (ClipboardManager) getSystemService(Context.CLIPBOARD_SERVICE);
    }

    private static String decode(Intent intent) {
        String b64 = intent.getStringExtra("b64");
        return b64 == null ? "" : new String(Base64.decode(b64, Base64.DEFAULT), StandardCharsets.UTF_8);
    }

    @Override
    public void onCreate() {
        super.onCreate();
        IntentFilter filter = new IntentFilter();
        filter.addAction(TEXT);
        filter.addAction(CLIP_SET);
        filter.addAction(CLIP_GET);
        if (Build.VERSION.SDK_INT >= 33) {
            registerReceiver(receiver, filter, Context.RECEIVER_EXPORTED);
        } else {
            registerReceiver(receiver, filter);
        }
    }

    @Override
    public void onDestroy() {
        unregisterReceiver(receiver);
        super.onDestroy();
    }

    @Override
    public boolean onEvaluateInputViewShown() {
        return false;
    }
}
