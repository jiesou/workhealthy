#include "lcd.h"
#include "interactive.h"

Board *board;
typedef struct
{
    lv_obj_t *card;
    lv_obj_t *title_label;
    lv_obj_t *desc_label;
} CardWidgets;

static CardWidgets ai_summary_card;
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
            lv_label_set_text(status_label, LV_SYMBOL_WIFI " 连接中");
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
        lv_obj_set_style_bg_opa(brightness_mask, LV_OPA_80, 0); // 人离开，遮罩变成灰色
    }
    else
    {
        lv_obj_set_style_bg_opa(brightness_mask, LV_OPA_0, 0); // 人到来，遮罩变成透明
    }
    lvgl_port_unlock();
}
void lcd_update_ai_summary(const char *text)
{
    if (ai_summary_card.desc_label != NULL)
    {
        lvgl_port_lock(-1);
        lv_label_set_text(ai_summary_card.desc_label, text);
        lv_obj_set_style_text_color(ai_summary_card.desc_label, lv_color_hex(0x888888), 0);
        lvgl_port_unlock();
    }
}
void lcd_update_cup_detect(const char *text)
{
    if (cup_detect_card.desc_label != NULL)
    {
        lvgl_port_lock(-1);
        lv_label_set_text(cup_detect_card.desc_label, text);
        lv_obj_set_style_text_color(cup_detect_card.desc_label, lv_color_hex(0x888888), 0);
        lvgl_port_unlock();
    }
}
void lcd_update_work_time(const char *text)
{
    if (work_time_card.desc_label != NULL)
    {
        lvgl_port_lock(-1);
        lv_label_set_text(work_time_card.desc_label, text);
        lvgl_port_unlock();
    }
}

CardWidgets _createCard(lv_obj_t *parent, const char *title, const char *description)
{
    CardWidgets widgets;
    widgets.card = lv_obj_create(parent);
    lv_obj_add_style(widgets.card, &container_style, NULL);
    lv_obj_add_style(widgets.card, &card_style, NULL);
    lv_obj_set_flex_grow(widgets.card, 1); // 让卡片自动伸展
    lv_obj_set_height(widgets.card, 130);  // card 初始高度，后续可以根据内容调整

    widgets.title_label = lv_label_create(widgets.card);
    lv_label_set_text(widgets.title_label, title);
    lv_obj_add_style(widgets.title_label, &card_style, NULL);
    lv_obj_add_style(widgets.title_label, &container_style, NULL);
    widgets.desc_label = lv_label_create(widgets.card);
    lv_label_set_text(widgets.desc_label, description);
    lv_obj_set_style_text_font(widgets.desc_label, &myfont_notosc_regular_16, NULL);
    lv_obj_set_style_text_color(widgets.desc_label, lv_color_hex(0x888888), NULL); // 灰色文字
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
    lv_obj_add_style(scr, &container_style, NULL);
    // lv_obj_set_style_pad_all(scr, 20, 0);
    lv_obj_set_flex_flow(scr, LV_FLEX_FLOW_COLUMN); // 垂直排列

    /* 1/8 title bar */
    lv_obj_t *title_bar = lv_obj_create(scr);
    lv_obj_add_style(title_bar, &container_style, NULL);
    lv_obj_set_flex_flow(title_bar, LV_FLEX_FLOW_ROW_WRAP); // 横向排列
    lv_obj_set_flex_align(title_bar, LV_FLEX_ALIGN_SPACE_AROUND, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER); // 分布到两端
    lv_obj_set_width(title_bar, LV_HOR_RES); // 宽度填满屏幕
    lv_obj_set_flex_grow(title_bar, 1);
    lv_obj_align(title_bar, LV_ALIGN_TOP_MID, 0, 0);
        /* title */
        lv_obj_t *title_label = lv_label_create(title_bar);
        lv_label_set_text(title_label, "工位天使 健康管理系统");
        lv_obj_add_style(title_label, &card_style, NULL);
        lv_obj_add_style(title_label, &container_style, NULL);
        /* status */
        status_label = lv_label_create(title_bar);
        lv_label_set_text(status_label, LV_SYMBOL_WIFI " 连接中");
        lv_obj_set_style_text_font(status_label, &myfont_notosc_regular_16, NULL);
    
    // 创建 4/8 功能区 Flex 容器（横向排列），并让子组件居中
    lv_obj_t *function_container = lv_obj_create(scr);
    lv_obj_add_style(function_container, &container_style, NULL);
    lv_obj_set_flex_flow(function_container, LV_FLEX_FLOW_ROW_WRAP); // 横向排列
    lv_obj_set_flex_align(function_container, LV_FLEX_ALIGN_SPACE_EVENLY, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER); // 均匀分布
    lv_obj_set_width(function_container, LV_HOR_RES); // 宽度填满屏幕
    lv_obj_set_flex_grow(function_container, 4);
    lv_obj_align_to(function_container, title_bar, LV_ALIGN_OUT_BOTTOM_MID, 0, 20);
        /* 节律光照提示文本 - 流光溢彩动画 1/3 */
        lv_obj_t *led_info_label = lv_label_create(function_container);
        lv_obj_add_style(led_info_label, &container_style, 0);
        lv_obj_set_flex_grow(led_info_label, 1); // 让空白区域自动伸展
        lv_obj_align(led_info_label, LV_ALIGN_CENTER, 0, 0);
        lv_label_set_text(led_info_label, "智能昼夜节律光照\n:) 专注模式\n屏幕蓝光抑制中");
        lv_obj_set_style_text_font(led_info_label, &myfont_notosc_regular_16, NULL);
        lv_obj_set_style_text_align(led_info_label, LV_TEXT_ALIGN_CENTER, NULL); // 文本居中
            lv_anim_t a;
            lv_anim_init(&a);
            lv_anim_set_var(&a, led_info_label); // 动画作用的对象
            lv_anim_set_exec_cb(&a, [](void *obj, int32_t v) {
                lv_obj_set_style_text_color((lv_obj_t *) obj, lv_color_mix(lv_color_hex(0x0045cd), lv_color_hex(0x52b3ff), v), 0);
            });
            lv_anim_set_time(&a, 2000);
            lv_anim_set_playback_time(&a, 2000); // 播放回来的时间（实现来回流光）
            lv_anim_set_repeat_count(&a, LV_ANIM_REPEAT_INFINITE); // 无限重复
            lv_anim_set_values(&a, 0, 255); // 动画值的范围，对应lv_color_mix的第三个参数

            lv_anim_start(&a);
        /* AI 摘要 Card 2/3 */
        ai_summary_card = _createCard(function_container, "AI 摘要", "正在准备...");
        lv_obj_set_flex_grow(ai_summary_card.card, 2); // 让 AI 摘要卡片自动伸展
        lv_obj_set_height(ai_summary_card.card, 170); // card 初始高度，后续可以根据内容调整
        lv_obj_set_width(ai_summary_card.desc_label, 220); // 固定描述字段的宽度，这样才能让文本自动换行
        lv_label_set_long_mode(ai_summary_card.desc_label, LV_LABEL_LONG_WRAP); // 文本换行
            lv_obj_t *ai_summary_btn = lv_btn_create(ai_summary_card.card);
            lv_obj_add_flag(ai_summary_btn, LV_OBJ_FLAG_FLOATING);      // 浮动对象，不参与布局流
            lv_obj_set_size(ai_summary_btn, 48, 48); // 按钮大小
            lv_obj_align_to(ai_summary_btn, ai_summary_card.card, LV_ALIGN_TOP_RIGHT, 10, 0); // 按钮在卡片右上角
                lv_obj_t *ai_summary_icon = lv_label_create(ai_summary_btn);
                lv_label_set_text(ai_summary_icon, LV_SYMBOL_REFRESH);
                lv_obj_set_style_text_font(ai_summary_icon, &myfont_notosc_regular_16, 0);
                lv_obj_center(ai_summary_icon);
            lv_obj_add_event_cb(ai_summary_btn, [](lv_event_t *e) {
                lcd_update_ai_summary("正在准备...");
                interactive_push_ai_summary_refresh();
            }, LV_EVENT_CLICKED, NULL); // 点击按钮刷新 AI 摘要

    // 创建 3/8 卡片 Flex 容器（横向排列），并让子组件居中
    lv_obj_t *cards_container = lv_obj_create(scr);
    lv_obj_add_style(cards_container, &container_style, 0);
    lv_obj_set_flex_flow(cards_container, LV_FLEX_FLOW_ROW); // 横向排列
    lv_obj_set_flex_align(cards_container, LV_FLEX_ALIGN_SPACE_EVENLY, LV_FLEX_ALIGN_START, LV_FLEX_ALIGN_CENTER); // 均匀分布
    lv_obj_set_width(cards_container, LV_HOR_RES); // 宽度填满屏幕
    lv_obj_set_flex_grow(cards_container, 3);
    lv_obj_align_to(cards_container, function_container, LV_ALIGN_OUT_BOTTOM_MID, 0, 20);

    /* 创建卡片 */
    cup_detect_card = _createCard(cards_container, "喝水检测", "未检测到水杯");
    work_time_card = _createCard(cards_container, "工作时间", "工作--");

    /* 亮度遮罩 */
    brightness_mask = lv_obj_create(lv_scr_act());
    lv_obj_remove_style_all(brightness_mask);
    
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
