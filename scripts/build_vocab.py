#!/usr/bin/env python3
"""Build data/vocab.json from the teaching list in this file.

Glosses, example sentences, and approximate CEFR bands are original to this
repository. They are study labels, not the Cambridge English Vocabulary
Profile or any Oxford word list. See DATA_SOURCES.md.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "vocab.json"

LEVELS = ("A1", "A2", "B1", "B2", "C1")
POS = {"noun", "verb", "adjective", "adverb", "conjunction", "interjection"}

# level, en, ipa, pos, vi, example, example_vi
ROWS: list[tuple[str, str, str, str, str, str, str]] = [
    ("A1", "hello", "/həˈləʊ/", "interjection", "xin chào", "Hello, my name is Mai.", "Xin chào, tên tôi là Mai."),
    ("A1", "water", "/ˈwɔːtə/", "noun", "nước", "Can I have a glass of water?", "Cho tôi một ly nước được không?"),
    ("A1", "food", "/fuːd/", "noun", "thức ăn", "The food is on the table.", "Thức ăn ở trên bàn."),
    ("A1", "house", "/haʊs/", "noun", "ngôi nhà", "Their house is near the school.", "Nhà họ ở gần trường."),
    ("A1", "family", "/ˈfæməli/", "noun", "gia đình", "I have a small family.", "Tôi có một gia đình nhỏ."),
    ("A1", "friend", "/frend/", "noun", "bạn", "She is my friend from class.", "Cô ấy là bạn cùng lớp của tôi."),
    ("A1", "book", "/bʊk/", "noun", "quyển sách", "This book is easy to read.", "Quyển sách này dễ đọc."),
    ("A1", "school", "/skuːl/", "noun", "trường học", "School starts at seven.", "Trường học bắt đầu lúc bảy giờ."),
    ("A1", "teacher", "/ˈtiːtʃə/", "noun", "giáo viên", "Our teacher speaks slowly.", "Giáo viên của chúng tôi nói chậm."),
    ("A1", "time", "/taɪm/", "noun", "thời gian", "What time is it?", "Mấy giờ rồi?"),
    ("A1", "day", "/deɪ/", "noun", "ngày", "Have a good day.", "Chúc một ngày tốt lành."),
    ("A1", "big", "/bɪɡ/", "adjective", "to", "This bag is too big.", "Cái túi này quá to."),
    ("A1", "small", "/smɔːl/", "adjective", "nhỏ", "They live in a small room.", "Họ sống trong một phòng nhỏ."),
    ("A1", "good", "/ɡʊd/", "adjective", "tốt", "That is a good idea.", "Đó là một ý hay."),
    ("A1", "eat", "/iːt/", "verb", "ăn", "We eat rice for lunch.", "Chúng tôi ăn cơm vào bữa trưa."),
    ("A1", "drink", "/drɪŋk/", "verb", "uống", "I drink tea in the morning.", "Tôi uống trà vào buổi sáng."),
    ("A1", "go", "/ɡəʊ/", "verb", "đi", "I go to school by bike.", "Tôi đi học bằng xe đạp."),
    ("A1", "come", "/kʌm/", "verb", "đến", "Please come in.", "Mời vào."),
    ("A1", "see", "/siː/", "verb", "nhìn thấy", "I can see the river.", "Tôi nhìn thấy dòng sông."),
    ("A1", "want", "/wɒnt/", "verb", "muốn", "I want a cup of tea.", "Tôi muốn một tách trà."),
    ("A2", "weather", "/ˈweðə/", "noun", "thời tiết", "The weather is hot today.", "Hôm nay thời tiết nóng."),
    ("A2", "travel", "/ˈtrævl/", "verb", "đi du lịch", "They travel by train.", "Họ đi du lịch bằng tàu hỏa."),
    ("A2", "ticket", "/ˈtɪkɪt/", "noun", "vé", "I bought a ticket online.", "Tôi mua vé trên mạng."),
    ("A2", "hospital", "/ˈhɒspɪtl/", "noun", "bệnh viện", "The hospital is on this street.", "Bệnh viện ở trên phố này."),
    ("A2", "healthy", "/ˈhelθi/", "adjective", "khỏe mạnh", "Fruit is healthy food.", "Trái cây là thức ăn tốt cho sức khỏe."),
    ("A2", "expensive", "/ɪkˈspensɪv/", "adjective", "đắt", "The shoes were expensive.", "Đôi giày đó đắt."),
    ("A2", "cheap", "/tʃiːp/", "adjective", "rẻ", "This market is cheap.", "Chợ này rẻ."),
    ("A2", "remember", "/rɪˈmembə/", "verb", "nhớ", "I remember your name.", "Tôi nhớ tên bạn."),
    ("A2", "forget", "/fəˈɡet/", "verb", "quên", "Don't forget your keys.", "Đừng quên chìa khóa."),
    ("A2", "borrow", "/ˈbɒrəʊ/", "verb", "mượn", "May I borrow your pen?", "Tôi mượn bút của bạn được không?"),
    ("A2", "lend", "/lend/", "verb", "cho mượn", "I can lend you an umbrella.", "Tôi có thể cho bạn mượn ô."),
    ("A2", "early", "/ˈɜːli/", "adjective", "sớm", "She arrived early.", "Cô ấy đến sớm."),
    ("A2", "late", "/leɪt/", "adjective", "muộn", "The bus is late.", "Xe buýt đến muộn."),
    ("A2", "busy", "/ˈbɪzi/", "adjective", "bận", "I am busy this afternoon.", "Chiều nay tôi bận."),
    ("A2", "quiet", "/ˈkwaɪət/", "adjective", "yên tĩnh", "The library is quiet.", "Thư viện yên tĩnh."),
    ("A2", "noisy", "/ˈnɔɪzi/", "adjective", "ồn ào", "The street is noisy at night.", "Đường phố ồn ào vào ban đêm."),
    ("A2", "journey", "/ˈdʒɜːni/", "noun", "hành trình", "The journey takes two hours.", "Hành trình mất hai giờ."),
    ("A2", "message", "/ˈmesɪdʒ/", "noun", "tin nhắn", "I sent you a message.", "Tôi đã gửi cho bạn một tin nhắn."),
    ("A2", "answer", "/ˈɑːnsə/", "noun", "câu trả lời", "That is the right answer.", "Đó là câu trả lời đúng."),
    ("A2", "practice", "/ˈpræktɪs/", "noun", "sự luyện tập", "Practice helps you remember.", "Luyện tập giúp bạn nhớ."),
    ("B1", "achieve", "/əˈtʃiːv/", "verb", "đạt được", "She worked hard to achieve her goal.", "Cô ấy đã làm việc chăm chỉ để đạt được mục tiêu."),
    ("B1", "although", "/ɔːlˈðəʊ/", "conjunction", "mặc dù", "Although it rained, we went out.", "Mặc dù trời mưa, chúng tôi vẫn ra ngoài."),
    ("B1", "available", "/əˈveɪləbl/", "adjective", "có sẵn", "This book is available at the library.", "Quyển sách này có sẵn ở thư viện."),
    ("B1", "benefit", "/ˈbenɪfɪt/", "noun", "lợi ích", "Exercise has a clear benefit.", "Tập thể dục có một lợi ích rõ ràng."),
    ("B1", "challenge", "/ˈtʃælɪndʒ/", "noun", "thử thách", "The exam was a real challenge.", "Kỳ thi đó là một thử thách thật sự."),
    ("B1", "consider", "/kənˈsɪdə/", "verb", "cân nhắc", "Please consider both options.", "Hãy cân nhắc cả hai lựa chọn."),
    ("B1", "develop", "/dɪˈveləp/", "verb", "phát triển", "The city will develop a new park.", "Thành phố sẽ phát triển một công viên mới."),
    ("B1", "environment", "/ɪnˈvaɪrənmənt/", "noun", "môi trường", "We should protect the environment.", "Chúng ta nên bảo vệ môi trường."),
    ("B1", "experience", "/ɪkˈspɪəriəns/", "noun", "kinh nghiệm", "She has experience as a teacher.", "Cô ấy có kinh nghiệm làm giáo viên."),
    ("B1", "opportunity", "/ˌɒpəˈtjuːnəti/", "noun", "cơ hội", "This job is a good opportunity.", "Công việc này là một cơ hội tốt."),
    ("B1", "require", "/rɪˈkwaɪə/", "verb", "yêu cầu", "The form requires your address.", "Mẫu đơn yêu cầu địa chỉ của bạn."),
    ("B1", "significant", "/sɪɡˈnɪfɪkənt/", "adjective", "đáng kể", "There was a significant change.", "Đã có một thay đổi đáng kể."),
    ("B1", "therefore", "/ˈðeəfɔː/", "adverb", "do đó", "It was late; therefore we left.", "Đã muộn; do đó chúng tôi ra về."),
    ("B1", "various", "/ˈveəriəs/", "adjective", "nhiều loại", "The shop sells various teas.", "Cửa hàng bán nhiều loại trà."),
    ("B1", "advice", "/ədˈvaɪs/", "noun", "lời khuyên", "Thank you for the advice.", "Cảm ơn lời khuyên của bạn."),
    ("B1", "compare", "/kəmˈpeə/", "verb", "so sánh", "Compare the two prices first.", "Hãy so sánh hai mức giá trước."),
    ("B1", "decision", "/dɪˈsɪʒn/", "noun", "quyết định", "It was a difficult decision.", "Đó là một quyết định khó."),
    ("B1", "encourage", "/ɪnˈkʌrɪdʒ/", "verb", "khuyến khích", "Teachers encourage students to ask.", "Giáo viên khuyến khích học sinh đặt câu hỏi."),
    ("B1", "improve", "/ɪmˈpruːv/", "verb", "cải thiện", "Daily practice will improve your listening.", "Luyện tập mỗi ngày sẽ cải thiện khả năng nghe."),
    ("B1", "manage", "/ˈmænɪdʒ/", "verb", "xoay xở", "He managed to finish on time.", "Anh ấy đã xoay xở để hoàn thành đúng giờ."),
    ("B1", "prevent", "/prɪˈvent/", "verb", "ngăn chặn", "A lock can prevent theft.", "Một ổ khóa có thể ngăn trộm."),
    ("B1", "suggest", "/səˈdʒest/", "verb", "gợi ý", "I suggest a short break.", "Tôi gợi ý nghỉ một chút."),
    ("B1", "population", "/ˌpɒpjuˈleɪʃn/", "noun", "dân số", "The population of the town is growing.", "Dân số của thị trấn đang tăng."),
    ("B1", "quality", "/ˈkwɒləti/", "noun", "chất lượng", "The quality of the water is good.", "Chất lượng nước tốt."),
    ("B2", "acknowledge", "/əkˈnɒlɪdʒ/", "verb", "thừa nhận", "She acknowledged the mistake.", "Cô ấy đã thừa nhận lỗi."),
    ("B2", "acquire", "/əˈkwaɪə/", "verb", "thu được", "He acquired the skill at work.", "Anh ấy thu được kỹ năng đó khi đi làm."),
    ("B2", "adequate", "/ˈædɪkwət/", "adjective", "đầy đủ", "The report is adequate for now.", "Bản báo cáo đủ dùng cho lúc này."),
    ("B2", "anticipate", "/ænˈtɪsɪpeɪt/", "verb", "dự đoán", "We anticipate a busy week.", "Chúng tôi dự đoán một tuần bận rộn."),
    ("B2", "coherent", "/kəʊˈhɪərənt/", "adjective", "mạch lạc", "Write a coherent paragraph.", "Hãy viết một đoạn văn mạch lạc."),
    ("B2", "compensate", "/ˈkɒmpenseɪt/", "verb", "bù đắp", "Nothing can compensate for the delay.", "Không gì bù đắp được sự chậm trễ."),
    ("B2", "criterion", "/kraɪˈtɪəriən/", "noun", "tiêu chí", "Cost is only one criterion.", "Chi phí chỉ là một tiêu chí."),
    ("B2", "elaborate", "/ɪˈlæbəreɪt/", "verb", "trình bày chi tiết", "Could you elaborate on that point?", "Bạn trình bày chi tiết ý đó được không?"),
    ("B2", "fluctuate", "/ˈflʌktʃueɪt/", "verb", "dao động", "Prices fluctuate during the year.", "Giá dao động trong năm."),
    ("B2", "hypothesis", "/haɪˈpɒθəsɪs/", "noun", "giả thuyết", "The hypothesis needs a test.", "Giả thuyết đó cần được kiểm tra."),
    ("B2", "implement", "/ˈɪmplɪment/", "verb", "triển khai", "The school will implement the plan.", "Nhà trường sẽ triển khai kế hoạch."),
    ("B2", "inevitable", "/ɪnˈevɪtəbl/", "adjective", "không thể tránh khỏi", "Some mistakes are inevitable.", "Một số lỗi là không thể tránh khỏi."),
    ("B2", "justify", "/ˈdʒʌstɪfaɪ/", "verb", "biện minh", "How do you justify the extra cost?", "Bạn biện minh cho khoản chi thêm thế nào?"),
    ("B2", "nonetheless", "/ˌnʌnðəˈles/", "adverb", "dù vậy", "It was hard; nonetheless, she continued.", "Việc đó khó; dù vậy, cô ấy vẫn tiếp tục."),
    ("B2", "perspective", "/pəˈspektɪv/", "noun", "góc nhìn", "From his perspective, the rule is fair.", "Theo góc nhìn của anh ấy, quy tắc đó công bằng."),
    ("B2", "preliminary", "/prɪˈlɪmɪnəri/", "adjective", "sơ bộ", "These are preliminary results.", "Đây là kết quả sơ bộ."),
    ("B2", "reluctant", "/rɪˈlʌktənt/", "adjective", "miễn cưỡng", "He was reluctant to speak.", "Anh ấy miễn cưỡng khi phải nói."),
    ("B2", "subsequent", "/ˈsʌbsɪkwənt/", "adjective", "tiếp theo", "Subsequent meetings were shorter.", "Các cuộc họp tiếp theo ngắn hơn."),
    ("B2", "undergo", "/ˌʌndəˈɡəʊ/", "verb", "trải qua", "The building will undergo repairs.", "Tòa nhà sẽ trải qua đợt sửa chữa."),
    ("B2", "undermine", "/ˌʌndəˈmaɪn/", "verb", "làm suy yếu", "Rumors can undermine trust.", "Tin đồn có thể làm suy yếu lòng tin."),
    ("B2", "versatile", "/ˈvɜːsətaɪl/", "adjective", "linh hoạt", "A versatile tool has many uses.", "Một dụng cụ linh hoạt có nhiều công dụng."),
    ("B2", "whereas", "/weərˈæz/", "conjunction", "trong khi đó", "I prefer tea, whereas she prefers coffee.", "Tôi thích trà, trong khi đó cô ấy thích cà phê."),
    ("B2", "maintain", "/meɪnˈteɪn/", "verb", "duy trì", "They maintain the old bridge.", "Họ duy trì chiếc cầu cũ."),
    ("B2", "consequence", "/ˈkɒnsɪkwəns/", "noun", "hậu quả", "Think about the consequence first.", "Hãy nghĩ đến hậu quả trước."),
    ("C1", "meticulous", "/məˈtɪkjələs/", "adjective", "tỉ mỉ", "She keeps meticulous notes.", "Cô ấy ghi chép rất tỉ mỉ."),
    ("C1", "ubiquitous", "/juːˈbɪkwɪtəs/", "adjective", "có mặt khắp nơi", "Phones are ubiquitous in the city.", "Điện thoại có mặt khắp nơi trong thành phố."),
    ("C1", "pragmatic", "/præɡˈmætɪk/", "adjective", "thực dụng", "We need a pragmatic solution.", "Chúng ta cần một giải pháp thực dụng."),
    ("C1", "scrutinize", "/ˈskruːtənaɪz/", "verb", "xem xét kỹ", "The editor scrutinized every line.", "Biên tập viên xem xét kỹ từng dòng."),
    ("C1", "exacerbate", "/ɪɡˈzæsəbeɪt/", "verb", "làm trầm trọng thêm", "The delay exacerbated the problem.", "Sự chậm trễ làm vấn đề trầm trọng thêm."),
    ("C1", "mitigate", "/ˈmɪtɪɡeɪt/", "verb", "giảm nhẹ", "Trees can mitigate the heat.", "Cây xanh có thể giảm bớt cái nóng."),
    ("C1", "prevalent", "/ˈprevələnt/", "adjective", "phổ biến", "This belief is still prevalent.", "Niềm tin này vẫn còn phổ biến."),
    ("C1", "inherent", "/ɪnˈhɪərənt/", "adjective", "vốn có", "There is an inherent risk.", "Có một rủi ro vốn có."),
    ("C1", "plausible", "/ˈplɔːzəbl/", "adjective", "hợp lý", "That explanation sounds plausible.", "Lời giải thích đó nghe hợp lý."),
    ("C1", "profound", "/prəˈfaʊnd/", "adjective", "sâu sắc", "The book had a profound effect.", "Cuốn sách có một ảnh hưởng sâu sắc."),
    ("C1", "arbitrary", "/ˈɑːbɪtrəri/", "adjective", "tùy tiện", "The cutoff felt arbitrary.", "Ngưỡng đó có vẻ tùy tiện."),
    ("C1", "comprehensive", "/ˌkɒmprɪˈhensɪv/", "adjective", "toàn diện", "We need a comprehensive review.", "Chúng ta cần một bài ôn toàn diện."),
    ("C1", "detrimental", "/ˌdetrɪˈmentl/", "adjective", "có hại", "Lack of sleep is detrimental.", "Thiếu ngủ thì có hại."),
    ("C1", "feasible", "/ˈfiːzəbl/", "adjective", "khả thi", "The plan is feasible this year.", "Kế hoạch khả thi trong năm nay."),
    ("C1", "negligible", "/ˈneɡlɪdʒəbl/", "adjective", "không đáng kể", "The difference is negligible.", "Mức chênh lệch không đáng kể."),
    ("C1", "unprecedented", "/ʌnˈpresɪdentɪd/", "adjective", "chưa từng có", "The storm caused unprecedented damage.", "Cơn bão gây thiệt hại chưa từng có."),
]


def slug(word: str) -> str:
    return "-".join(word.strip().lower().split())


def build() -> list[dict[str, str]]:
    cards: list[dict[str, str]] = []
    seen: set[str] = set()
    for level, en, ipa, pos, vi, example, example_vi in ROWS:
        if level not in LEVELS:
            raise SystemExit(f"unknown level: {level}")
        if pos not in POS:
            raise SystemExit(f"unknown part of speech for {en}: {pos}")
        for label, value in (
            ("en", en),
            ("vi", vi),
            ("example", example),
            ("example_vi", example_vi),
        ):
            if not value.strip():
                raise SystemExit(f"empty {label} for {en}")
            if "\t" in value:
                raise SystemExit(f"tab in {label} for {en}")
        card_id = slug(en)
        if card_id in seen:
            raise SystemExit(f"duplicate id: {card_id}")
        seen.add(card_id)
        cards.append(
            {
                "id": card_id,
                "en": en,
                "ipa": ipa,
                "pos": pos,
                "vi": vi,
                "example": example,
                "exampleVi": example_vi,
                "level": level,
            }
        )
    order = {level: index for index, level in enumerate(LEVELS)}
    cards.sort(key=lambda card: (order[card["level"]], card["en"]))
    return cards


def main() -> None:
    cards = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(cards, ensure_ascii=False, indent=2) + "\n"
    if "--check" in sys.argv:
        current = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if current != payload:
            raise SystemExit("data/vocab.json is out of date; run scripts/build_vocab.py")
        print(f"{len(cards)} cards match {OUT.relative_to(ROOT)}")
        return
    OUT.write_text(payload, encoding="utf-8")
    print(f"wrote {len(cards)} cards to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
