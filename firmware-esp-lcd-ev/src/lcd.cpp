#include "lcd.h"

// 按钮点击事件回调函数
static void button_event_handler(lv_event_t *e)
{
    lv_event_code_t code = lv_event_get_code(e);
    lv_obj_t *btn = lv_event_get_target(e); // 获取触发事件的对象

    if (code == LV_EVENT_CLICKED)
    {
        Serial.println("Button Clicked!");
        // 可以在这里更新其他UI元素或执行其他操作
        lv_obj_t *label = lv_obj_get_child(btn, 0); // 获取按钮上的标签
        lv_label_set_text(label, "Clicked!");       // 改变按钮文本
    }
}

void _createUI()
{
    Serial.println("Creating UI");
    /* Lock the mutex due to the LVGL APIs are not thread-safe */
    lvgl_port_lock(-1);

    lv_obj_t *label = lv_label_create(lv_scr_act());
    lv_label_set_text_fmt(
        label, "ESP32_Display_Panel(%d.%d.%d)",
        ESP_PANEL_VERSION_MAJOR, ESP_PANEL_VERSION_MINOR, ESP_PANEL_VERSION_PATCH);
    lv_obj_set_style_text_font(label, &lv_font_montserrat_14, 0);
    lv_obj_align(label, LV_ALIGN_CENTER, 0, -50); // 调整位置，给按钮留出空间

    // 创建一个按钮
    lv_obj_t *btn = lv_btn_create(lv_scr_act()); // 在当前屏幕上创建按钮
    lv_obj_set_size(btn, 120, 50);               // 设置按钮大小
    lv_obj_align(btn, LV_ALIGN_CENTER, 0, 20);   // 调整按钮位置

    // 在按钮上添加一个标签
    lv_obj_t *btn_label = lv_label_create(btn);
    lv_label_set_text(btn_label, "Click Me!");
    lv_obj_center(btn_label); // 标签在按钮内部居中

    // 添加事件回调函数
    lv_obj_add_event_cb(btn, button_event_handler, LV_EVENT_CLICKED, NULL);

    lvgl_port_unlock();
}

void lcd_init()
{
    Serial.println("Initializing board");
    Board *board = new Board();
    board->init();
    assert(board->begin());

    Serial.println("Initializing LVGL");
    lvgl_port_init(board->getLCD(), board->getTouch());

    Serial.println("Creating UI");
    _createUI();
}
