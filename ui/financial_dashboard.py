"""Standalone dashboard: python -m streamlit run ui/financial_dashboard.py."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import cast

# Streamlit executes this file with ui/ on sys.path, including outside the repo cwd.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import altair as alt
import pandas as pd
import streamlit as st

from ui.financial_results import (
    DEFAULT_RUN,
    RESULTS_ROOT,
    aggregate_results,
    discover_tests,
    load_collection,
    paired_changes,
    paired_questions,
)

METRICS = {
    'qa_accuracy': 'QA accuracy · higher is better',
    'bits_per_byte': 'Bits per byte · lower is better',
    'seconds': 'Evaluation seconds · lower is better',
    'peak_allocated_gib': 'Peak allocated GiB · lower is better',
}
MODE_COLOR = alt.Scale(domain=['baseline', 'adapted'], range=['#92a6b8', '#16a085'])


def comparison_chart(frame: pd.DataFrame, metric: str) -> alt.Chart:
    frame = frame.copy()
    frame['configuration'] = frame['model']
    if frame.duplicated(['model', 'mode']).any() and 'model_id' in frame:
        frame['configuration'] = (frame['model'].astype(str) + ' · ' + frame['model_id'].astype(str)
                                  + ' · ' + frame['dtype'].astype(str))
    return alt.Chart(frame).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
        x=alt.X('configuration:N', title=None), xOffset='mode:N',
        y=alt.Y(f'{metric}:Q', title=METRICS[metric], scale=alt.Scale(zero=True),
                axis=alt.Axis(format='.0%') if metric == 'qa_accuracy' else alt.Axis()),
        color=alt.Color('mode:N', scale=MODE_COLOR, title='Configuration'),
        tooltip=['model:N', 'mode:N', alt.Tooltip(f'{metric}:Q', format='.3f')],
    ).properties(height=290)


def main() -> None:
    st.set_page_config(page_title='Financial pilot · Evaluation', page_icon='📊', layout='wide')
    st.title('Financial pilot evaluation')
    st.caption('Baseline → adaptation · Financial text modeling and literal amount extraction')
    run_paths = discover_tests()
    if not run_paths:
        st.error(f'No saved comparison.json files found under {RESULTS_ROOT}.')
        return
    tests = {str(p.relative_to(RESULTS_ROOT)): p for p in run_paths}
    default = str(DEFAULT_RUN.relative_to(RESULTS_ROOT))
    options = list(tests) + ['All tests']
    choice = st.sidebar.selectbox('Evaluation test', options,
                                  index=options.index(default) if default in options else 0,
                                  key='evaluation_test')
    aggregate = choice == 'All tests'
    paths = run_paths if aggregate else [tests[choice]]
    st.sidebar.caption(f'{len(paths)} test folder(s) selected')
    data = load_collection(paths)
    if not data.rows:
        for issue in data.issues:
            st.error(issue)
        return
    for issue in data.issues:
        st.warning(issue)
    models = sorted({r['model'] for r in data.rows})
    selected = st.sidebar.multiselect('Model families', models, default=models, key='models')
    modes = st.sidebar.multiselect('Configurations', ['baseline', 'adapted'], default=['baseline', 'adapted'], key='modes')
    st.sidebar.caption('All views follow these filters. Paired views require both configurations.')
    display_rows = aggregate_results(data) if aggregate else data.rows
    frame = pd.DataFrame([r for r in display_rows if r['model'] in selected and r['mode'] in modes])
    if frame.empty:
        st.info('Select at least one model family and configuration.')
        return
    st.warning('These extraction evaluations do not measure broad financial reasoning or establish statistical significance.')
    if aggregate:
        st.info('All tests: QA is weighted by question count; bits per byte is weighted by UTF-8 bytes. Repeated questions count again. Evaluation time is summed and peak memory is the maximum. Model IDs and dtypes remain separate.')
        st.caption('Pooled results can combine different suites or adapter checkpoints and are exploratory. Adaptation deltas are calculated within each original test.')
    best_qa = frame.loc[frame.qa_accuracy.idxmax()]
    bpb_rows = frame.dropna(subset=['bits_per_byte'])
    best_bpb = bpb_rows.loc[bpb_rows.bits_per_byte.idxmin()] if not bpb_rows.empty else None
    cards = st.columns(4)
    cards[0].metric('Configurations shown', len(frame))
    cards[1].metric('Highest QA accuracy', f'{best_qa.qa_accuracy:.0%}')
    cards[1].caption(f'{best_qa.model} / {best_qa["mode"]} (ties possible)')
    cards[2].metric('Lowest bits per byte', f'{best_bpb.bits_per_byte:.3f}' if best_bpb is not None else 'Unavailable')
    cards[2].caption(f'{best_bpb.model} / {best_bpb["mode"]}' if best_bpb is not None else 'Complete passage samples required')
    cards[3].metric('Questions per configuration', ' / '.join(str(n) for n in sorted(frame.question_count.unique())))
    overview, adaptation, answers, prose, provenance = st.tabs([
        'Overview', 'Adaptation impact', 'Answer explorer', 'Passage scores', 'Protocol & provenance',
    ])
    with overview:
        left, right = st.columns(2)
        with left:
            st.altair_chart(comparison_chart(frame, 'qa_accuracy'), width='stretch')
        with right:
            st.altair_chart(comparison_chart(frame, 'bits_per_byte'), width='stretch')
        st.subheader('Quality and resource comparison')
        columns = ['test', 'test_count', 'suite_count', 'model', 'model_id', 'mode', 'qa_accuracy', 'bits_per_byte', 'seconds', 'peak_allocated_gib',
                   'model_parameters', 'document_count', 'question_count', 'dtype']
        st.dataframe(frame[[c for c in columns if c in frame]], hide_index=True, width='stretch',
                     column_config={'qa_accuracy': st.column_config.NumberColumn('QA accuracy', format='%.2f'),
                                    'seconds': 'Evaluation seconds', 'peak_allocated_gib': 'Peak allocated GiB'})
        st.caption('QA accuracy is a fraction (0–1). Seconds cover harness scoring after model loading; GiB is peak PyTorch CUDA allocation. Neither is training cost or controlled inference throughput.')
        st.download_button('Download filtered comparison CSV', frame.to_csv(index=False), 'financial_comparison.csv', 'text/csv')
        resource = st.selectbox('Resource metric', ['seconds', 'peak_allocated_gib'], format_func=lambda key: METRICS[key])
        st.altair_chart(comparison_chart(frame, resource), width='stretch')
    with adaptation:
        changes = pd.DataFrame(paired_changes([r for r in data.rows if r['model'] in selected and r['mode'] in modes]))
        if changes.empty:
            st.info('Select baseline and adapted configurations from a matching suite to see paired changes.')
        else:
            st.caption('Changes are adapted minus baseline. Positive QA percentage points and negative bits-per-byte changes indicate improvement.')
            for metric, title in [('qa_change_pp', 'QA accuracy change (percentage points)'), ('bpb_change', 'Bits-per-byte change')]:
                chart = alt.Chart(changes).mark_bar().encode(
                    x=alt.X('model:N', title=None), xOffset='test:N', y=alt.Y(f'{metric}:Q', title=title),
                    color=alt.condition(f'datum.{metric} {">=" if metric == "qa_change_pp" else "<="} 0', alt.value('#16a085'), alt.value('#c0392b')),
                    tooltip=['test:N', 'model:N', alt.Tooltip(f'{metric}:Q', format='.3f')],
                ).properties(height=230)
                st.altair_chart(chart, width='stretch')
            st.dataframe(changes, hide_index=True, width='stretch')
            st.caption('BPB reduction (%) = 100 × (baseline − adapted) / baseline. No aggregate winner is computed across these different metrics.')
    with answers:
        st.caption('Saved whole-response scores are preserved. Numeric scales normalize, but currency, units, and extra explanation can change correctness. Raw output is shown with whitespace intact.')
        model = st.selectbox('Inspect model', selected, key='question_model')
        answer_test = st.selectbox('Answer test', list(data.config['tests']), key='answer_test')
        samples = [r for r in data.qa if r['mode'] in modes and r['test'] == answer_test]
        pairs = paired_questions(samples, str(model))
        transition = st.selectbox('Answer outcome', ['All', 'Improved', 'Regressed', 'Both correct', 'Both incorrect', 'Unpaired'], key='transition')
        query = st.text_input('Search question, passage, reference, or response')
        matching = [p for p in pairs if (transition == 'All' or p['transition'] == transition)
                    and query.casefold() in json.dumps(p, ensure_ascii=False).casefold()]
        st.caption(f'{len(matching)} matching questions')
        if matching:
            st.dataframe(pd.DataFrame(matching)[['id', 'transition', 'baseline_correct', 'adapted_correct', 'baseline_response', 'adapted_response']], hide_index=True, width='stretch')
            question_id = st.selectbox('Question', [p['id'] for p in matching])
            question = next(p for p in matching if p['id'] == question_id)
            st.text(question['question'])
            st.text(question['context'])
            st.write('Accepted answers:', question['answers'])
            for col, mode in zip(st.columns(2), ['baseline', 'adapted']):
                with col:
                    st.subheader(mode.capitalize())
                    score = question[f'{mode}_correct']
                    st.caption('Missing' if score is None else 'Correct' if score else 'Incorrect')
                    response = question[f'{mode}_response']
                    st.code(response if response is not None else '(No saved response)', language=None)
            st.download_button('Download matching answers', json.dumps(matching, indent=2, ensure_ascii=False), 'financial_answers.json', 'application/json')
        else:
            st.info('No questions match these filters, or saved samples are unavailable.')
    with prose:
        st.caption('Per-passage BPB = −log likelihood / (UTF-8 bytes × ln 2). The headline BPB weights by byte count; it is not the arithmetic mean of passage scores.')
        passage_test = st.selectbox('Passage test', list(data.config['tests']), key='passage_test')
        passages = pd.DataFrame([r for r in data.prose if r['model'] in selected and r['mode'] in modes and r['test'] == passage_test])
        if passages.empty:
            st.info('No saved passage scores are available.')
        else:
            st.dataframe(passages.drop(columns=['text']), hide_index=True, width='stretch')
            passage_id = st.selectbox('Inspect passage', sorted(passages.id.unique()))
            st.text(passages[passages.id == passage_id].iloc[0]['text'])
            st.altair_chart(comparison_chart(cast(pd.DataFrame, passages.loc[passages.id == passage_id]), 'bits_per_byte'), width='stretch')
    with provenance:
        st.write('This pilot uses greedy generation, no chat template, and a shared 1,024-token context budget. Different tokenizers still affect rolling windows. Model sizes differ; BPB is not an isolated architecture test.')
        st.write('Training/validation exact document hashes were excluded when building the frozen suite. Near duplicates and contamination from original base-model pretraining are not ruled out.')
        provenance_test = st.selectbox('Provenance test', list(data.config['tests']))
        config = data.config['tests'][provenance_test]
        if config.get('note'):
            st.info(config['note'])
        st.caption('The evaluation GPU below is distinct from GPUs recorded for training each adapter.')
        st.json({k: v for k, v in config.items() if k != 'runs'})
        for run_config in config.get('runs', []):
            if run_config.get('label') in selected:
                with st.expander(f"{run_config['label']} · training configuration and artifact hashes"):
                    st.json(run_config)
        st.download_button('Download evaluation configuration', json.dumps(data.config, indent=2), 'evaluation_config.json', 'application/json')


if __name__ == '__main__':
    main()
