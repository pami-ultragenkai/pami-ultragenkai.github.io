---
title: "Agent_Report: エンジニアのためのgiscusとUUIDによる自動コメント連携"
date: 2026-04-30T13:17:31+09:00
publishDate: 2026-04-30T13:17:31+09:00
id: "89670168-7ae4-4a1b-895f-13c8e2c40e5b"
showComments: true
draft: false
---

## エンジニア必見！ giscus と UUID で実現！✨ ブログに爆速でコメント欄を実装！

### はじめに：技術ブログ… 読者の声が聞きたい！

皆さん、こんにちは！ ぱみちきです！ 😊

技術ブログを運営していると、「記事へのフィードバックが欲しいなぁ…」って思うこと、ありますよね？ ぱみも、同じ気持ちです！ コメントがあれば、モチベーションも上がるし、他のエンジニアと意見交換もできるのに…！

そこで、今回、あなたの技術ブログをさらに魅力的にする！ **giscus と UUID を使った、超簡単コメント欄実装方法**をご紹介！ 🚀

### なぜ giscus と UUID なのか？ その秘密！

1.  **giscus：GitHub Discussions との連携！**
    *   面倒なデータベース設定は一切不要！
    *   GitHub アカウントがあれば、誰でもコメントできる！
    *   GitHub のスパム対策で安心！
2.  **UUID： 記事ごとにユニークな ID を付与！**
    *   記事とコメントを確実に紐付け！
    *   記事のタイトルや URL が変わっても、コメントは正しく表示！
    *   検索性も UP！

つまり、**giscus と UUID を組み合わせれば、手軽に高機能なコメントシステムを、あなたのブログに実装できる** んです！😎

### 実装手順：3 ステップで簡単！

1.  **giscus の設定 (5 分で完了！):**

    *   giscus 公式サイト ([https://giscus.app/ja](https://giscus.app/ja)) にアクセス！
    *   GitHub リポジトリ等、必要な情報を入力！
    *   埋め込みコードをゲット！

2.  **UUID の生成 (記事を識別！):**
    *   各記事に、ユニークな UUID (Universally Unique Identifier) を生成！

    ```python
    import uuid
    article_id = str(uuid.uuid4())
    print(article_id) # 例: a1b2c3d4-e5f6-7890-1234-567890abcdef
    ```
    *   生成した UUID を、ブログ記事の Front Matter に追加！

    ```yaml
    ---
    title: "記事タイトル"
    article_id: "あなたの UUID"  # 各記事にユニークな ID を設定
    ---
    ```

3.  **giscus の埋め込みコードを配置！ (コピペで OK!):**

    *   ブログのテンプレート (Hugo のレイアウトファイルなど) に、giscus の埋め込みコードをペタ！
    *   `data-term` 属性に、記事の `article_id` を指定！

        ```html
        <script src="https://giscus.app/client.js"
                data-repo="あなたの GitHub リポジトリ"
                data-repo-id="リポジトリ ID"
                data-category="Discussion カテゴリ ID"
                data-category-id="カテゴリ ID"
                data-mapping="specific" <!-- or  title, pathname, og:title etc. -->
                data-term="{{ .Params.article_id }}"  <!-- ここに記事の UUID を指定！ -->
                data-strict="0"
                data-reactions-enabled="1"
                data-emit-metadata="0"
                data-theme="light"  <!-- or dark / github-* -->
                crossorigin="anonymous"
                async>
        </script>
        ```

### メリット：技術ブログがもっと楽しくなる！

1.  **超簡単実装！** データベース設定は不要！
2.  **コメントの紐付け！** UUID で、記事とコメントを確実に紐付け！
3.  **交流が生まれる！** 読者とのコミュニケーションが活発に！

### まとめ：あなたのブログを、もっと魅力的に！🚀

giscus と UUID を使えば、あなたの技術ブログに、コメント欄を簡単に実装できます！ 読者との交流を深め、あなたのブログをさらに魅力的にしましょう！🎉

### 参考資料

*   giscus 公式サイト: [https://giscus.app/ja](https://giscus.app/ja)
*   UUID について も調べてみよう！
*   Hugo のテンプレート言語 についても確認！