# Nguồn dữ liệu

Bộ thẻ trong `data/vocab.json` được tạo bởi `scripts/build_vocab.py`. Ngày đối chiếu giấy phép và ngày tải dùng cho bản trong repo: **13 tháng 11 năm 2026**.

Mỗi nguồn dưới đây được đọc trực tiếp (trang giấy phép hoặc lời ghi trên trang tải) trước khi dùng. Không dùng nguồn nào mà giấy phép không rõ.

## 1. Wiktionary tiếng Việt, qua kaikki.org

| | |
|---|---|
| Dùng để | Nghĩa tiếng Việt và IPA của mục từ tiếng Anh |
| URL dữ liệu | https://kaikki.org/viwiktionary/rawdata.html |
| File | https://kaikki.org/viwiktionary/raw-wiktextract-data.jsonl.gz |
| Wiktionary | https://vi.wiktionary.org/ |
| Giấy phép | **CC BY-SA 4.0** và **GFDL** |

Đã kiểm tra:

- Chân trang Wiktionary tiếng Việt ghi văn bản được phát hành theo giấy phép Creative Commons Ghi công – Chia sẻ tương tự, và liên kết tới https://creativecommons.org/licenses/by-sa/4.0/deed.vi (cùng bản tiếng Anh của giấy phép 4.0).
- Trang bản quyền Wiktionary tiếng Anh (https://en.wiktionary.org/wiki/Wiktionary:Copyrights) nói các mục từ được cấp đồng thời theo CC BY-SA 4.0 và GNU Free Documentation License. Bản trích này dùng theo CC BY-SA 4.0, có ghi công và nêu phần đã sửa.
- kaikki.org (https://kaikki.org/viwiktionary/index.html) nói bản trích giữ nguyên giấy phép của Wiktionary (CC BY-SA và GFDL). Trang raw data ghi dump viwiktionary ngày 2026-10-02.

Phần đã sửa so với bản gốc: chỉ giữ mục từ tiếng Anh có trong danh sách CEFR bên dưới; chọn một nghĩa ngắn, bỏ chú thích trong ngoặc, bỏ mục tục/lỗi thời; ưu tiên IPA kiểu Mỹ khi có nhãn; bỏ phiên âm không phải IPA.

## 2. CEFR-J Wordlist, phiên bản 1.5

| | |
|---|---|
| Dùng để | Mức A1–B2 và nhãn chủ đề |
| URL | https://www.cefr-j.org/download.html |
| Bản dùng trong script | https://github.com/openlanguageprofiles/olp-en-cefrj/blob/master/cefrj-vocabulary-profile-1.5.csv |
| Giấy phép | Bản quyền phòng thí nghiệm Yukio Tono, Đại học Ngoại ngữ Tokyo (TUFS). **Được dùng miễn phí cho nghiên cứu, giáo dục và cả mục đích thương mại nếu trích dẫn.** Được phép sửa để lập bảng từ khác, với điều kiện vẫn trích dẫn bảng gốc. |

Đã kiểm tra trên https://www.cefr-j.org/download.html (bản tiếng Anh của lời ghi cho Wordlist 1.6, cùng điều kiện sử dụng) và README của kho Open Language Profiles, mục Terms of use, ngày 13/11/2026. Script dùng phiên bản 1.5 vì đó là file CSV được kho này phát hành lại kèm lời trích dẫn.

Trích dẫn:

> The CEFR-J Wordlist Version 1.5. Compiled by Yukio Tono, Tokyo University of Foreign Studies. Retrieved via https://github.com/openlanguageprofiles/olp-en-cefrj on 13/11/2026. Original project page: https://www.cefr-j.org/download.html

Mức trong bảng là mức CEFR-J, không phải chứng chỉ của Hội đồng Châu Âu hay Cambridge. Bản CEFR-J có đối chiếu với English Vocabulary Profile khi các tác giả lập bảng; app này không chép định nghĩa hay văn bản của English Vocabulary Profile.

## 3. Octanove Vocabulary Profile C1/C2, phiên bản 1.0

| | |
|---|---|
| Dùng để | Mức C1 và C2 |
| URL | https://github.com/openlanguageprofiles/olp-en-cefrj/blob/master/octanove-vocabulary-profile-c1c2-1.0.csv |
| Tác giả dữ liệu | Octanove Labs |
| Giấy phép | **CC BY-SA 4.0** — https://creativecommons.org/licenses/by-sa/4.0/ |

Đã kiểm tra README của https://github.com/openlanguageprofiles/olp-en-cefrj (mục Terms of use): “The Octanove Vocabulary Profile for C1/C2 levels can be used under a Creative Commons Attribution-ShareAlike 4.0 International License.”

## 4. Tatoeba

| | |
|---|---|
| Dùng để | Câu ví dụ tiếng Anh và bản dịch tiếng Việt |
| URL | https://tatoeba.org/en/downloads |
| File | https://downloads.tatoeba.org/exports/per_language/vie/vie_sentences_detailed.tsv.bz2 |
| | https://downloads.tatoeba.org/exports/per_language/vie/vie-eng_links.tsv.bz2 |
| | https://downloads.tatoeba.org/exports/per_language/eng/eng_sentences_detailed.tsv.bz2 |
| Giấy phép | **CC BY 2.0 Pháp** — https://creativecommons.org/licenses/by/2.0/fr/ |

Đã kiểm tra trang tải: “These files are released under CC BY 2.0 FR.” Cùng trang nói nhiều câu tiếng Anh và tiếng Nhật đến từ Tanaka Corpus, thuộc phạm vi công cộng. Mỗi câu trong app giữ id Tatoeba và tên người viết khi file xuất có tên. Trang **Nguồn** và dòng nhỏ trên mặt sau thẻ là chỗ ghi công.

Câu chỉ được gắn vào thẻ khi chứa đúng từ, hoặc một dạng chia đơn giản (số nhiều, -ed, -ing). Không phải từ nào cũng có câu.

## Cách các giấy phép đứng cạnh nhau

- Nghĩa, IPA, và việc chọn từ C1/C2 là nội dung chia sẻ tương tự. Bản `vocab.json` phát hành phần đó theo **CC BY-SA 4.0**.
- Câu ví dụ giữ **CC BY 2.0 FR** của Tatoeba (ghi tên tác giả và id).
- Mức A1–B2 và chủ đề lấy từ CEFR-J theo giấy phép riêng của TUFS: dùng được, kể cả thương mại, miễn là giữ lời trích dẫn ở trên. Giấy phép đó không phải Creative Commons.

Mã nguồn app (HTML, CSS, JS, script tạo dữ liệu) là MIT, xem `LICENSE`. MIT không bao gồm `data/vocab.json` hay font.

## Font

Be Vietnam Pro và Fraunces (SIL Open Font License 1.1). Bản OFL nằm trong `fonts/OFL-BeVietnamPro.txt` và `fonts/OFL-Fraunces.txt`.
