"""Build-time scroll markup preserves authored content and native table layout."""

from html.parser import HTMLParser
import unittest

from builder.markdown import to_html


class ScrollMarkupTests(unittest.TestCase):
    def test_markdown_table_and_code_are_labelled_without_forcing_focus(self):
        body, _ = to_html("| A | B |\n| :- | -: |\n| x | y |\n\n```python\nx = 1\n```")
        self.assertIn('<div class="table-scroll" data-scroll-label="Table 1: scroll horizontally to explore"><table>', body)
        self.assertIn('style="text-align: right;"', body)
        self.assertIn('data-scroll-label="Code example 1: scroll horizontally to explore"', body)
        self.assertNotIn("tabindex", body)
        self.assertNotIn('role="region"', body)

    def test_nested_and_adjacent_authored_tables_keep_balanced_wrappers(self):
        inner = '<table><tr><td>Inner &amp; intact</td></tr></table>'
        outer = '<TABLE title="one > two"><tr><td>' + inner + '</td></tr></TABLE>'
        next_table = '<table><tr><td>Next</td></tr></table>'
        body, _ = to_html(outer + next_table)
        self.assertEqual(body.count('class="table-scroll"'), 3)
        self.assertIn('<TABLE title="one > two">', body)
        self.assertIn(inner + '</div></td></tr></TABLE></div><div', body.replace('\n', ''))
        self.assertTrue(body.endswith(next_table + '</div>'))

    def test_existing_wrappers_and_labels_are_preserved(self):
        source = ('<div class="custom table-scroll" data-scroll-label="Comparison">'
                  '<table><tr><td>Data</td></tr></table></div>')
        body, _ = to_html(source)
        self.assertEqual(body, source)
        unlabelled = source.replace(' data-scroll-label="Comparison"', '')
        body, _ = to_html(unlabelled)
        self.assertEqual(body.count('table-scroll'), 1)
        self.assertIn('data-scroll-label="Table 1:', body)
        self.assertEqual(to_html(body)[0], body)

    def test_mermaid_classes_are_tokens_and_existing_code_labels_survive(self):
        source = ('<pre class="extra mermaid">graph LR\nA --&gt; B</pre>\n\n'
                  '<pre data-scroll-label="Custom example"><code>&lt;table&gt;</code></pre>\n\n'
                  '<pre class="mermaid-example"><code>Ordinary code</code></pre>')
        body, _ = to_html(source)
        pre_attrs = []

        class Pres(HTMLParser):
            def handle_starttag(self, tag, attrs):
                if tag == "pre":
                    pre_attrs.append(dict(attrs))

        parser = Pres()
        parser.feed(body)
        self.assertNotIn("data-scroll-label", pre_attrs[0])
        self.assertEqual(pre_attrs[1]["data-scroll-label"], "Custom example")
        self.assertEqual(pre_attrs[2]["data-scroll-label"], "Code example 2: scroll horizontally to explore")
        self.assertIn("&lt;table&gt;", body)

    def test_comments_and_code_examples_do_not_become_tables(self):
        comment = '<!-- <table><tr><td>Hidden</td></tr></table><pre>Hidden</pre> -->'
        body, _ = to_html(comment + '\n\n```html\n<table><tr><td>Example</td></tr></table>\n```')
        self.assertIn(comment, body)
        self.assertNotIn('class="table-scroll"', body)
        self.assertIn('data-scroll-label="Code example 1:', body)
        self.assertIn('&lt;table&gt;', body)


if __name__ == "__main__":
    unittest.main()
