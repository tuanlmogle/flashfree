# Nguồn dữ liệu

Bộ thẻ nằm trong `data/meta.json` và `data/level-a1.json` … `data/level-c2.json`, tạo bởi `scripts/build_vocab.py` và `scripts/build_images.py`. Ngày đối chiếu giấy phép cho bản trong repo: **14 tháng 11 năm 2026** (các nguồn cũ đối chiếu lần đầu ngày 13 tháng 11 năm 2026, xem lại cùng ngày 14).

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

## 5. wordfreq

| | |
|---|---|
| Dùng để | Xếp mức A1–C2 cho từ không có trong CEFR-J hoặc Octanove, theo tần suất |
| URL | https://github.com/rspeer/wordfreq |
| Tác giả | Robyn Speer |
| Giấy phép dữ liệu | **CC BY-SA 4.0** — https://creativecommons.org/licenses/by-sa/4.0/ |
| Mã nguồn gói | Apache 2.0 (không nhúng mã vào trang web) |

Đã kiểm tra `NOTICE.md` trên nhánh master ngày 14/11/2026. File đó nói dữ liệu tần suất được phân phối theo CC BY-SA 4.0, và yêu cầu ghi công Robyn Speer đúng tên này. Cùng file liệt kê nguồn gốc:

- Google Books Ngram Viewer — lời ghi trên trang dữ liệu, được wordfreq trích lại: dùng tự do cho mọi mục đích, nên ghi nhận và dẫn tới https://books.google.com/ngrams
- Wikipedia (CC BY-SA)
- ParaCrawl — https://paracrawl.eu
- Leeds Internet Corpus — http://corpus.leeds.ac.uk/list.html
- OPUS OpenSubtitles 2018, ghi nhận OpenSubtitles — http://www.opensubtitles.org/
- SUBTLEX (US, UK và các bảng cùng nhóm) của Marc Brysbaert và cộng sự. wordfreq ghi rằng tác giả đã được phép phân phối các bảng này cho mọi mục đích, không chỉ nghiên cứu, với điều kiện ghi tên SUBTLEX và nói rõ dữ liệu được cung cấp tự do.

App không nhúng bảng tần suất thô. Mỗi từ mới nhận một mức bằng cách so Zipf của nó với trung vị Zipf của từ CEFR-J/Octanove cùng thang A1–C2.

## 6. Open English WordNet 2024

Phần chủ đề giữ như mục dưới. Thêm: câu giải nghĩa tiếng Anh ngắn cho từ không có gloss tiếng Việt cũng lấy từ định nghĩa synset của lexicon `oewn:2024` (**CC BY 4.0**). Câu được rút gọn (bỏ chú thích trong ngoặc, cắt khoảng 110 ký tự). Thẻ đó được đánh dấu `meaningLang: "en"`.

## 6b. Bộ biểu tượng trên thẻ

Máy không tải cả bộ ảnh vào repo. `data/emoji-index.json` chỉ ghi mã emoji và đường dẫn Fluent. Trình duyệt xin từng hình khi thẻ hiện ra.

| Bộ | Dùng để | Bản ghim | Giấy phép |
|---|---|---|---|
| Microsoft Fluent Emoji | Sticker 3D | commit `1ffb34c752ecf5d402f04cfb4b392c77f57c54bc` | **MIT** — https://github.com/microsoft/fluentui-emoji/blob/main/LICENSE |
| Twemoji | Emoji phẳng | tag `14.0.2` | **CC BY 4.0** cho hình (README kho twitter/twemoji). Mã nguồn kho ghi MIT. |
| Google Noto Emoji | Emoji phẳng | tag `v2.047` | **SIL OFL 1.1** theo README của https://github.com/googlefonts/noto-emoji (đã đọc 14/11/2026). Không phải Apache. |
| OpenMoji | Emoji màu, có tên người vẽ | `17.0.0` | **CC BY-SA 4.0** |
| Wikimedia Commons | Ảnh thật của danh từ, đã chọn ở vòng trước | file và giấy phép nằm trên từng thẻ | Từng ảnh: PD, CC0, CC BY, CC BY-SA hoặc GFDL |

Đã kiểm tra Fluent: file `LICENSE` ở gốc kho là MIT, và URL `.../Red apple/3D/red_apple_3d.png` trả về 200. Twemoji: README nói graphics licensed under CC-BY 4.0. Noto: README nói Open Font License 1.1.

## 6d. Từ chuyên ngành (Ngành nghề)

Các file `data/fields/*.json` chỉ tải khi người học mở chủ đề đó, hoặc tải nền sau màn hình đầu. Id thẻ cũ trong `data/level-*.json` không đổi; script chỉ thêm mã chủ đề.

| Nguồn | Dùng để | Giấy phép |
|---|---|---|
| NGSL, NAWL, BSL, TSL — Charles Browne, Brent Culligan, Joseph Phillips | Gắn từ học thuật, thương mại, TOEIC vào ngành khi từ khớp lĩnh vực | **CC BY-SA 4.0**. Trang https://www.newgeneralservicelist.com/ ghi dùng tự do, kể cả thương mại, nếu ghi công. Bản mirror TextMeter cũng ghi CC BY-SA 4.0. Không dùng Coxhead AWL hay danh sách Oxford/Cambridge. |
| Trang Glossary của Wikipedia tiếng Anh và phụ lục thuật ngữ Wiktionary tiếng Anh | Thuật ngữ, kể cả cụm nhiều chữ, cùng câu giải nghĩa ngắn | **CC BY-SA 4.0** |
| MeSH 2025 (Medical Subject Headings), Thư viện Y khoa Quốc gia Hoa Kỳ | Thuật ngữ y, giải phẫu, dược, nha, điều dưỡng | Phạm vi công cộng (tác phẩm của chính phủ Hoa Kỳ). https://www.nlm.nih.gov/mesh/ |
| Open English WordNet 2024 | Thêm từ chuyên hơn bằng quan hệ hạ vị (hyponym) và câu giải nghĩa tiếng Anh khi không có tiếng Việt | **CC BY 4.0** |
| Wiktionary tiếng Việt (kaikki) | Nghĩa tiếng Việt của từ mới | **CC BY-SA 4.0** và GFDL |
| Tatoeba | Câu ví dụ khi có | **CC BY 2.0 FR** |
| wordfreq (Robyn Speer) | Xếp mức CEFR cho từ không có trong CEFR-J hoặc Octanove | **CC BY-SA 4.0** |

Mức chính thức của CEFR-J và Octanove được giữ. Từ chuyên ngành không có mức chính thức dùng cùng các ngưỡng Zipf trong `scripts/build_vocab.py` (C1 từ 2.70).

## 6e. Cụm động từ, thành ngữ, và cụm từ hay đi chung

Hai chủ đề, tải khi người học mở chúng (`data/fields/deck-phrasal.json` và `data/fields/deck-collocation.json`). Id thẻ cũ không đổi.

| Nguồn | Dùng để | Giấy phép |
|---|---|---|
| Wiktionary tiếng Anh, bản trích kaikki.org (wiktextract) | Cụm động từ và thành ngữ, kể cả nhãn phrasal / idiomatic, và bản dịch tiếng Việt nếu mục có | **CC BY-SA 4.0** và GFDL. Bỏ mục ghi British-only, archaic, obsolete, rare, hoặc dated. |
| Wiktionary tiếng Việt (kaikki) | Nghĩa tiếng Việt khi có | **CC BY-SA 4.0** và GFDL |
| Open English WordNet 2024 | Câu giải nghĩa tiếng Anh khi không có tiếng Việt | **CC BY 4.0** |
| Tatoeba câu tiếng Anh–Việt | Câu ví dụ, và đếm số câu chứa **cả cụm** (không tách từng từ) để xếp mức và thứ tự | **CC BY 2.0 FR** |

Mức của hai chủ đề này lấy từ số lần cả cụm xuất hiện trong Tatoeba, trải từ A2 (cụm gặp hàng ngày) đến C2 (cụm hiếm). Cụm không có câu nào, tiếng lóng/thô tục, hoặc mẫu `someone`/`something` không thông dụng thì bỏ. Trong một mức, thẻ có câu ví dụ đứng trước. wordfreq không dùng để xếp mức cụm, vì nó cộng tần suất từng từ chứ không phải tần suất cả cụm.

Cụm động từ và thành ngữ nằm chung một chủ đề, **Cụm động từ & thành ngữ**. Cụm từ hay đi chung là chủ đề thứ hai. `run out of` không có mục riêng trên Wiktionary; thẻ `run out` phủ cách dùng đó. Không dùng danh sách Oxford, Cambridge, hay sách thành ngữ có bản quyền.

## 6c. Open English WordNet, mục phân loại

| | |
|---|---|
| Dùng để | Gán chủ đề bằng synset và quan hệ thượng vị |
| URL | https://github.com/globalwordnet/english-wordnet |
| Giấy phép | **CC BY 4.0** — https://creativecommons.org/licenses/by/4.0/ |

Đã kiểm tra trường license của lexicon `oewn:2024` trong gói `wn` ngày 14/11/2026: `https://creativecommons.org/licenses/by/4.0`. Danh sách từ thủ công trong `scripts/topics.py` là phần chọn của app, không phải văn bản WordNet.

## 7. OpenMoji 17.0.0

| | |
|---|---|
| Dùng để | Minh họa trên thẻ khi không có ảnh Commons phù hợp |
| URL | https://openmoji.org/ |
| Dữ liệu | https://github.com/hfg-gmuend/openmoji |
| Giấy phép | **CC BY-SA 4.0** — https://creativecommons.org/licenses/by-sa/4.0/ |

Đã kiểm tra `LICENSE.txt` của kho ngày 14/11/2026 (văn bản CC BY-SA 4.0) và bản phát hành 17.0.0 (23/04/2026). SVG được tải lúc xem thẻ từ jsDelivr, không commit vào repo. Nút **i** trên thẻ ghi tên người vẽ trong dữ liệu OpenMoji.

## 8. Wikimedia Commons, qua trang Wikipedia tiếng Anh

| | |
|---|---|
| Dùng để | Ảnh danh từ (bản thu nhỏ rộng khoảng 320px) |
| API | https://en.wikipedia.org/w/api.php và https://commons.wikimedia.org/w/api.php |
| Giấy phép | Từng ảnh một: phạm vi công cộng, CC0, CC BY, CC BY-SA hoặc GFDL |

App không chép văn bản bài Wikipedia. Trang Wikipedia chỉ dùng để tìm ảnh đại diện tự do (`page_image_free`) của mục từ danh từ, rồi giấy phép và tác giả lấy từ metadata Commons. Ảnh không rõ giấy phép, giấy phép cấm thương mại hoặc cấm sửa, trang định hướng, và một số mục từ mà ảnh dễ gây hiểu nhầm bị bỏ. Tên tác giả, mã giấy phép và tên file nằm trong dữ liệu thẻ; nút **i** hiện chúng cùng liên kết tới trang file.

## Cách các giấy phép đứng cạnh nhau

- Nghĩa, IPA, việc chọn từ C1/C2, và mức xếp từ tần suất wordfreq là nội dung chia sẻ tương tự khi nguồn yêu cầu. Các file `data/level-*.json` phát hành phần đó theo **CC BY-SA 4.0**.
- Câu ví dụ giữ **CC BY 2.0 FR** của Tatoeba (ghi tên tác giả và id).
- Mức A1–B2 của từ có trong CEFR-J theo giấy phép riêng của TUFS: dùng được, kể cả thương mại, miễn là giữ lời trích dẫn ở trên. Giấy phép đó không phải Creative Commons.
- Chủ đề có phần dựa trên Open English WordNet (**CC BY 4.0**).
- Ảnh OpenMoji giữ **CC BY-SA 4.0**. Ảnh Commons giữ đúng giấy phép ghi trên từng thẻ.

Mã nguồn app (HTML, CSS, JS, script tạo dữ liệu) là MIT, xem `LICENSE`. MIT không bao gồm `data/vocab.json` hay font.

## Font

Be Vietnam Pro và Fraunces (SIL Open Font License 1.1). Bản OFL nằm trong `fonts/OFL-BeVietnamPro.txt` và `fonts/OFL-Fraunces.txt`.
