package com.phonemcp.fixture;

import android.app.Activity;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.res.Configuration;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Bundle;
import android.text.Editable;
import android.text.TextWatcher;
import android.util.Log;
import android.view.GestureDetector;
import android.view.MotionEvent;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageButton;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.Switch;
import android.widget.TextView;

import java.util.Locale;

public final class MainActivity extends Activity {
    private static final String TAG = "PhoneMcpFixture";
    private TextView status;
    private SharedPreferences prefs;
    private float dragX, dragY;

    private void set(String s) {
        status.setText(s);
        Log.i(TAG, s);
    }

    private int bump() {
        int n = prefs.getInt("taps", 0) + 1;
        prefs.edit().putInt("taps", n).apply();
        return n;
    }

    private Button button(int id, String label) {
        Button b = new Button(this);
        b.setId(id);
        b.setText(label);
        b.setAllCaps(false);
        return b;
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        prefs = getSharedPreferences("fixture", MODE_PRIVATE);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setFitsSystemWindows(true);

        status = new TextView(this);
        status.setId(R.id.status);
        status.setTextSize(18);
        root.addView(status);

        EditText field = new EditText(this);
        field.setId(R.id.field);
        field.setHint("Type here");
        field.setSingleLine(true);
        field.addTextChangedListener(new TextWatcher() {
            @Override public void beforeTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void onTextChanged(CharSequence s, int a, int b, int c) {}
            @Override public void afterTextChanged(Editable s) { Log.i(TAG, "field=" + s); }
        });
        field.setOnEditorActionListener((v, action, event) -> { set("submit:" + v.getText()); return false; });
        root.addView(field);

        Button tap = button(R.id.tap_btn, "Tap me");
        tap.setOnClickListener(v -> set("tap:" + bump()));
        root.addView(tap);

        Button where = button(R.id.where_btn, "Where");
        where.setOnClickListener(v -> {
            LocationManager locations = (LocationManager) getSystemService(LOCATION_SERVICE);
            try {
                locations.requestLocationUpdates(LocationManager.GPS_PROVIDER, 0, 0f, (LocationListener) fix ->
                        set(String.format(Locale.US, "loc:%.2f,%.2f", fix.getLatitude(), fix.getLongitude())));
                set("listening");
            } catch (SecurityException e) {
                set("loc:denied");
            }
        });
        root.addView(where);

        ImageButton icon = new ImageButton(this);
        icon.setId(R.id.icon_btn);
        icon.setImageResource(android.R.drawable.ic_menu_add);
        icon.setOnClickListener(v -> set("icon"));
        root.addView(icon);

        Button hold = button(R.id.hold_btn, "Hold me");
        hold.setOnLongClickListener(v -> { set("long"); return true; });
        root.addView(hold);

        Button dbl = button(R.id.double_btn, "Double me");
        GestureDetector gd = new GestureDetector(this, new GestureDetector.SimpleOnGestureListener() {
            @Override public boolean onDoubleTap(MotionEvent e) { set("double"); return true; }
        });
        dbl.setOnTouchListener((v, e) -> gd.onTouchEvent(e));
        root.addView(dbl);

        Switch toggle = new Switch(this);
        toggle.setId(R.id.toggle);
        toggle.setText("Toggle");
        toggle.setOnCheckedChangeListener((v, on) -> set("switch:" + (on ? "on" : "off")));
        root.addView(toggle);

        TextView drag = new TextView(this);
        drag.setId(R.id.drag_area);
        drag.setText("Drag area");
        drag.setBackgroundColor(0xFFDDDDFF);
        drag.setPadding(16, 60, 16, 60);
        drag.setOnTouchListener((v, e) -> {
            if (e.getAction() == MotionEvent.ACTION_DOWN) {
                dragX = e.getRawX();
                dragY = e.getRawY();
            } else if (e.getAction() == MotionEvent.ACTION_UP) {
                set("drag:" + Math.round(e.getRawX() - dragX) + "," + Math.round(e.getRawY() - dragY));
            }
            return true;
        });
        root.addView(drag);

        LinearLayout list = new LinearLayout(this);
        list.setOrientation(LinearLayout.VERTICAL);
        for (int i = 1; i <= 60; i++) {
            TextView row = new TextView(this);
            row.setText("Item " + i);
            row.setTextSize(20);
            row.setPadding(16, 24, 16, 24);
            list.addView(row);
        }
        ScrollView scroll = new ScrollView(this);
        scroll.addView(list);
        root.addView(scroll, new LinearLayout.LayoutParams(-1, 0, 1f));
        setContentView(root);

        boolean night = (getResources().getConfiguration().uiMode & Configuration.UI_MODE_NIGHT_MASK)
                == Configuration.UI_MODE_NIGHT_YES;
        set("ready taps=" + prefs.getInt("taps", 0) + " night=" + night);
        handle(getIntent());
    }

    @Override
    protected void onNewIntent(Intent intent) {
        super.onNewIntent(intent);
        handle(intent);
    }

    private void handle(Intent intent) {
        if (intent != null && intent.getData() != null) set("url:" + intent.getData());
    }

    @Override
    public void onConfigurationChanged(Configuration c) {
        super.onConfigurationChanged(c);
        boolean night = (c.uiMode & Configuration.UI_MODE_NIGHT_MASK) == Configuration.UI_MODE_NIGHT_YES;
        set("config night=" + night + " land=" + (c.orientation == Configuration.ORIENTATION_LANDSCAPE));
    }
}
