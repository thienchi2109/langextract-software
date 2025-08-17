{
  "name": "public_health_generic_v1",
  "prompt_description": "Nhiệm vụ: Trích xuất **chính xác** các trường theo *schema người dùng* từ báo cáo **y tế công cộng** (giám sát dịch tễ, tiêm chủng, nhập viện, tử vong, xét nghiệm…).

Quy tắc:
1) **Không bịa/diễn giải**; chỉ dùng thông tin **có trong văn bản**.
2) **Khoá số & đơn vị**: giữ nguyên số liệu và ký hiệu như nguồn (%, ca, tử vong, nhập viện, liều, /100.000 dân, tuần, ngày, RR, OR, CI 95%, p=…). Không quy đổi đơn vị, không làm tròn.
3) **Ngữ cảnh đúng**: khi có nhiều kỳ/địa bàn, ưu tiên giá trị khớp **kỳ báo cáo và địa bàn** mô tả trong trường; nếu mơ hồ → để trống.
4) **Riêng tư**: giữ nguyên các chuỗi **[MASK]**; **không** khôi phục hay suy đoán thông tin nhận dạng cá nhân.
5) **Trả về chuỗi trích dẫn đúng** (faithful). Với trường kiểu `number`, nếu schema yêu cầu **số thuần**, chỉ lấy phần số từ văn bản (ví dụ: ‘75,3%’ → ‘75.3’; ‘1.250 ca’ → ‘1250’).
6) **Ngày/kỳ**: giữ định dạng gốc (ví dụ: ‘Tuần 32/2025’, ‘01–07/08/2025’).
7) **Nhóm tuổi/địa danh/viết tắt**: giữ nguyên như văn bản (ví dụ: ‘≥65’, ‘0–4’, ‘ICU’, ‘TP. Hồ Chí Minh’).
8) Nếu không tìm thấy thông tin cho một trường → **để trống**.

Chỉ trích xuất theo **danh sách trường** của schema; **không** tạo trường mới.",
  "fields": [
    {"name": "dia_ban", "type": "text", "description": "Tỉnh/thành/quận/huyện hoặc cơ sở y tế"},
    {"name": "ky_bao_cao", "type": "text", "description": "Ngày/tuần/tháng/quý của báo cáo"},
    {"name": "benh", "type": "text", "description": "Tên bệnh/chủ đề (vd: sốt xuất huyết, COVID‑19)"},
    {"name": "so_ca_moi", "type": "number", "description": "Số ca mắc mới trong kỳ"},
    {"name": "so_tu_vong", "type": "number", "description": "Số tử vong trong kỳ"},
    {"name": "ti_le_duong_tinh", "type": "number", "description": "% mẫu xét nghiệm dương tính"},
    {"name": "ti_le_tiem_chung", "type": "number", "description": "% bao phủ tiêm chủng (nếu có)"},
    {"name": "nhap_vien", "type": "number", "optional": true, "description": "Số ca nhập viện trong kỳ"},
    {"name": "nhan_xet_chinh", "type": "text", "optional": true, "description": "Tóm tắt 1–2 ý quan trọng (ổ dịch mới, xu hướng)"}
  ],
  "examples": [
    {
      "text": "Báo cáo tuần 32/2025: Hà Nội ghi nhận 1.250 ca sốt xuất huyết mới (↑12% so với tuần trước), 2 tử vong. Tỷ lệ dương tính RT‑PCR: 18,7%. Bao phủ tiêm vắc xin sởi mũi 1 đạt 95,2% ở nhóm 12–23 tháng.",
      "extractions": [
        {"class": "dia_ban", "text": "Hà Nội"},
        {"class": "ky_bao_cao", "text": "Tuần 32/2025"},
        {"class": "benh", "text": "sốt xuất huyết"},
        {"class": "so_ca_moi", "text": "1250"},
        {"class": "so_tu_vong", "text": "2"},
        {"class": "ti_le_duong_tinh", "text": "18.7"},
        {"class": "ti_le_tiem_chung", "text": "95.2"}
      ]
    }
  ],
  "provider": {"type": "gemini", "model_id": "gemini-2.5-pro", "api_base": "https://generativelanguage.googleapis.com"},
  "run_options": {"max_workers": 8, "extraction_passes": 2, "max_char_buffer": 1200}
}