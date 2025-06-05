#include "lcd.h"

Board *board;
typedef struct
{
    lv_obj_t *card;
    lv_obj_t *title_label;
    lv_obj_t *desc_label;
} CardWidgets;

static CardWidgets cup_detect_card;
static CardWidgets work_time_card;
static lv_obj_t *status_label;
static lv_obj_t *brightness_mask = nullptr;

/* 卡片的 style */
lv_style_t card_style;
/* 没有边框 container 的 style */
lv_style_t container_style;

void lcd_update_connect_status(const bool connected)
{
    if (status_label != NULL)
    {
        lvgl_port_lock(-1);
        if (connected)
        {
            lv_label_set_text(status_label, LV_SYMBOL_OK " 已连接");
            lv_obj_set_style_text_color(status_label, lv_color_hex(0x00FF00), 0);
        }
        else
        {
            lv_label_set_text(status_label, LV_SYMBOL_WIFI " 未连接");
            lv_obj_set_style_text_color(status_label, lv_color_hex(0xFF0000), 0);
        }

        lvgl_port_unlock();
    }
}
void lcd_update_person_detected(const bool person_detected)
{
    lvgl_port_lock(-1);
    if (!person_detected)
    {
        lv_obj_set_style_bg_opa(brightness_mask, LV_OPA_60, 0); // 人离开，遮罩变成灰色
    }
    else
    {
        lv_obj_set_style_bg_opa(brightness_mask, LV_OPA_0, 0); // 人到来，遮罩变成透明
    }
    lvgl_port_unlock();
}
void lcd_update_cup_detect(const bool cup_detected)
{
    if (cup_detect_card.desc_label != NULL)
    {
        lvgl_port_lock(-1);
        char buf[64];
        snprintf(buf, sizeof(buf), "检测到 %s", cup_detected ? "杯子" : "无杯子");
        lv_label_set_text(cup_detect_card.desc_label, buf);
        lvgl_port_unlock();
    }
}
void lcd_update_work_time(const char *text)
{
    if (work_time_card.desc_label != NULL)
    {
        lvgl_port_lock(-1);
        char buf[64];
        snprintf(buf, sizeof(buf), "工作时间 %s 秒", text);
        lv_label_set_text(work_time_card.desc_label, buf);
        lvgl_port_unlock();
    }
}

CardWidgets _createCard(lv_obj_t *parent, const char *title, const char *description)
{
    CardWidgets widgets;
    widgets.card = lv_obj_create(parent);
    lv_obj_add_style(widgets.card, &container_style, 0);
    lv_obj_add_style(widgets.card, &card_style, 0);
    lv_obj_set_flex_grow(widgets.card, 1); // 让卡片自动伸展
    lv_obj_set_height(widgets.card, 150);  // card 初始高度，后续可以根据内容调整

    widgets.title_label = lv_label_create(widgets.card);
    lv_label_set_text(widgets.title_label, title);
    lv_obj_add_style(widgets.title_label, &card_style, 0);
    lv_obj_add_style(widgets.title_label, &container_style, 0);

    widgets.desc_label = lv_label_create(widgets.card);
    lv_label_set_text(widgets.desc_label, description);
    lv_obj_set_style_text_font(widgets.desc_label, &myfont_notosc_regular_16, 0);
    lv_obj_set_style_text_color(widgets.desc_label, lv_color_hex(0x888888), 0); // 灰色文字
    lv_obj_align_to(widgets.desc_label, widgets.title_label, LV_ALIGN_OUT_BOTTOM_MID, 0, 20);

    return widgets;
}

void _createUI()
{
    // clang-format off
    /* Lock the mutex due to the LVGL APIs are not thread-safe */
    lvgl_port_lock(-1);
    lv_disp_set_rotation(lv_disp_get_default(), LV_DISP_ROT_180);

    /* 初始化样式 */
    lv_style_init(&card_style);
    lv_style_set_radius(&card_style, 15); // 注意：非 LV_DRAW_COMPLEX 模式无法绘制圆角
    lv_style_set_flex_flow(&card_style, LV_FLEX_FLOW_COLUMN); // 垂直排列
    lv_style_set_border_width(&card_style, 3); // 边框宽度
    lv_style_set_height(&card_style, LV_SIZE_CONTENT); // 高度自适应
    lv_style_set_text_font(&card_style, &myfont_notosc_bold_24);

    lv_style_init(&container_style);
    lv_style_set_border_width(&container_style, 0); // 无边框
    // lv_style_set_bg_opa(&container_style, LV_OPA_TRANSP); // 背景透明
    lv_style_set_layout(&container_style, LV_LAYOUT_FLEX); // 子布局 Flex


    /* 覆盖屏幕的默认样式，使其成为一个干净的布局容器 */
    lv_obj_t *scr = lv_scr_act();
    lv_obj_add_style(scr, &container_style, 0);
    // lv_obj_set_style_pad_all(scr, 20, 0);
    lv_obj_set_flex_flow(scr, LV_FLEX_FLOW_COLUMN); // 垂直排列

    /* title bar */
    lv_obj_t *title_bar = lv_obj_create(scr);
    lv_obj_add_style(title_bar, &container_style, 0);
    lv_obj_set_flex_flow(title_bar, LV_FLEX_FLOW_ROW_WRAP); // 横向排列
    lv_obj_set_flex_align(title_bar, LV_FLEX_ALIGN_SPACE_AROUND, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER); // 分布到两端
    lv_obj_set_width(title_bar, LV_HOR_RES); // 宽度填满屏幕
    lv_obj_align(title_bar, LV_ALIGN_TOP_MID, 0, 0);
        /* title */
        lv_obj_t *title_label = lv_label_create(title_bar);
        lv_label_set_text(title_label, "工位天使 健康管理系统");
        lv_obj_add_style(title_label, &card_style, 0);
        lv_obj_add_style(title_label, &container_style, 0);
        /* status */
        status_label = lv_label_create(title_bar);
        lv_label_set_text(status_label, LV_SYMBOL_WIFI " 未连接");
        lv_obj_set_style_text_font(status_label, &myfont_notosc_regular_16, 0);

    // 创建 Flex 容器（横向排列），并让子组件居中
    lv_obj_t *cards_container = lv_obj_create(scr);
    lv_obj_add_style(cards_container, &container_style, 0);
    lv_obj_set_flex_flow(cards_container, LV_FLEX_FLOW_ROW); // 横向排列
    lv_obj_set_flex_align(cards_container, LV_FLEX_ALIGN_SPACE_EVENLY, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER); // 均匀分布
    lv_obj_set_width(cards_container, LV_HOR_RES); // 宽度填满屏幕
    lv_obj_set_flex_grow(cards_container, 1); // 让卡片自动伸展
    lv_obj_align_to(cards_container, title_bar, LV_ALIGN_OUT_BOTTOM_MID, 0, 20);

    /* 创建卡片 */
    cup_detect_card = _createCard(cards_container, "喝水检测", "检测到--，喝水时间--");
    work_time_card = _createCard(cards_container, "工作时间", "工作--");


    brightness_mask = lv_obj_create(lv_scr_act()); // 创建遮罩对象在当前屏幕
    lv_obj_remove_style_all(brightness_mask);      // 移除默认样式
    
    // 设置为不参与布局计算
    lv_obj_clear_flag(brightness_mask, LV_OBJ_FLAG_CLICKABLE);   // 不可点击
    lv_obj_add_flag(brightness_mask, LV_OBJ_FLAG_FLOATING);      // 浮动对象，不参与布局流
    lv_obj_add_flag(brightness_mask, LV_OBJ_FLAG_OVERFLOW_VISIBLE); // 允许内容超出边界
    
    // 设置全屏大小 & 居中
    lv_obj_set_size(brightness_mask, LV_HOR_RES, LV_VER_RES);
    lv_obj_set_pos(brightness_mask, 0, 0);  // 从左上角开始
    
    // 设置黑色 + 初始透明
    lv_obj_set_style_bg_color(brightness_mask, lv_color_black(), 0);
    lv_obj_set_style_bg_opa(brightness_mask, LV_OPA_0, 0); // 初始全透明
    
    // 保证始终在最上面
    lv_obj_move_foreground(brightness_mask);

    lvgl_port_unlock();
    // clang-format on
}

void lcd_init()
{
    ESP_LOGI(TAG, "Initializing board");
    board = new Board();
    board->init();
    assert(board->begin());

    ESP_LOGI(TAG, "Initializing LVGL");
    lvgl_port_init(board->getLCD(), board->getTouch());

    ESP_LOGI(TAG, "Creating UI");
    _createUI();
}
