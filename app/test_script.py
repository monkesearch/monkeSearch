#!/usr/bin/env python3
"""
Simple test suite for monkeSearch query parser (llama_cpp implementation)
Run: python test_monke_llamacpp.py
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from query_gen import QueryExtractor


def test_query(extractor, query, expected_file_types, expected_temporal_unit=None, 
               expected_temporal_value=None, test_name=""):
    """Test a single query"""
    result_json = extractor.llm_query_gen(query)
    result = json.loads(result_json)
    
    # Check file types
    file_types_match = set(result["file_types"]) == set(expected_file_types)
    
    # Check temporal
    temporal_match = True
    has_temporal = expected_temporal_unit is not None
    
    if expected_temporal_unit:
        # Both time_unit and time_unit_value should match
        temporal_match = (result.get("time_unit", "") == expected_temporal_unit and
                         result.get("time_unit_value", "") == expected_temporal_value)
    else:
        # Should have empty strings for temporal fields
        temporal_match = (not result.get("time_unit") or result.get("time_unit") == "") and \
                        (not result.get("time_unit_value") or result.get("time_unit_value") == "")
    
    passed = file_types_match and temporal_match
    
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status} {test_name}")
    print(f"    Query: '{query}'")
    if not passed:
        print(f"    Expected file_types: {expected_file_types}, Got: {result['file_types']}")
        if expected_temporal_unit:
            expected_temp = f"{expected_temporal_unit}:{expected_temporal_value}"
            actual_temp = f"{result.get('time_unit', '')}:{result.get('time_unit_value', '')}"
            print(f"    Expected temporal: {expected_temp}, Got: {actual_temp}")
    
    return passed, has_temporal


def main():
    print("=" * 70)
    print("MONKESEARCH TEST SUITE - 30 Test Cases (llama_cpp)")
    print("=" * 70)
    print()
    
    extractor = QueryExtractor()
    results_no_temporal = []
    results_with_temporal = []
    
    # Test 1-5: File types only (NO TEMPORAL)
    print("File Type Tests (No Temporal):")
    print("-" * 70)
    
    passed, has_temp = test_query(extractor, "pdf files", ["pdf"], 
                                  test_name="Test 1: PDF files")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "python scripts", ["py"], 
                                  test_name="Test 2: Python scripts")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "images", ["jpg", "png"], 
                                  test_name="Test 3: Images (generic)")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "excel spreadsheets", ["xlsx"], 
                                  test_name="Test 4: Excel files")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "videos", ["mp4", "avi"], 
                                  test_name="Test 5: Videos (generic)")
    results_no_temporal.append(passed)
    
    print()
    
    # Test 6-10: Temporal only (WITH TEMPORAL)
    print("Temporal Tests:")
    print("-" * 70)
    
    passed, has_temp = test_query(extractor, "files from yesterday", [], "days", "1",
                                  test_name="Test 6: Yesterday")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "from 3 days ago", [], "days", "3",
                                  test_name="Test 7: 3 days ago")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "last week", [], "weeks", "1",
                                  test_name="Test 8: Last week")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "7 months ago", [], "months", "7",
                                  test_name="Test 9: 7 months ago")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "2 years ago", [], "years", "2",
                                  test_name="Test 10: 2 years ago")
    results_with_temporal.append(passed)
    
    print()
    
    # Test 11-15: Combined queries (WITH TEMPORAL)
    print("Combined Tests (File Type + Temporal):")
    print("-" * 70)
    
    passed, has_temp = test_query(extractor, "python scripts from 3 days ago", ["py"], "days", "3",
                                  test_name="Test 11: Python + 3 days ago")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "photos from yesterday", ["jpg", "png"], "days", "1",
                                  test_name="Test 12: Photos + yesterday")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "pdf 7 months ago", ["pdf"], "months", "7",
                                  test_name="Test 13: PDF + 7 months ago")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "images from last week", ["jpg", "png"], "weeks", "1",
                                  test_name="Test 14: Images + last week")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "excel files from 2 years ago", ["xlsx"], "years", "2",
                                  test_name="Test 15: Excel + 2 years ago")
    results_with_temporal.append(passed)
    
    print()
    
    # Test 16-20: More realistic file type queries (NO TEMPORAL)
    print("Realistic File Type Tests:")
    print("-" * 70)
    
    passed, has_temp = test_query(extractor, "markdown and text documents", ["md", "txt"],
                                  test_name="Test 16: Markdown and text")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "all my code files", ["py", "js", "java", "cpp"],
                                  test_name="Test 17: Generic code files")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "presentations", ["pptx", "ppt"],
                                  test_name="Test 18: Presentations")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "audio files", ["mp3", "wav", "flac"],
                                  test_name="Test 19: Audio files")
    results_no_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "word documents", ["docx", "doc"],
                                  test_name="Test 20: Word documents")
    results_no_temporal.append(passed)
    
    print()
    
    # Test 21-25: More realistic temporal queries (WITH TEMPORAL)
    print("Realistic Temporal Tests:")
    print("-" * 70)
    
    passed, has_temp = test_query(extractor, "files from last month", [], "months", "1",
                                  test_name="Test 21: Last month")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "from the past 2 weeks", [], "weeks", "2",
                                  test_name="Test 22: Past 2 weeks")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "files from today", [], "days", "0",
                                  test_name="Test 23: Today")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "6 months back", [], "months", "6",
                                  test_name="Test 24: 6 months back")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "files modified this year", [], "years", "1",
                                  test_name="Test 25: This year")
    results_with_temporal.append(passed)
    
    print()
    
    # Test 26-30: More realistic combined queries (WITH TEMPORAL)
    print("Realistic Combined Tests:")
    print("-" * 70)
    
    passed, has_temp = test_query(extractor, "word documents from last month", ["docx", "doc"], "months", "1",
                                  test_name="Test 26: Word docs + last month")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "javascript files from this week", ["js"], "weeks", "1",
                                  test_name="Test 27: JS files + this week")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "all pdfs from the past year", ["pdf"], "years", "1",
                                  test_name="Test 28: PDFs + past year")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "csv files from 2 months ago", ["csv"], "months", "2",
                                  test_name="Test 29: CSV + 2 months ago")
    results_with_temporal.append(passed)
    
    passed, has_temp = test_query(extractor, "video files from yesterday", ["mp4", "avi"], "days", "1",
                                  test_name="Test 30: Videos + yesterday")
    results_with_temporal.append(passed)
    
    # Summary
    print()
    print("=" * 70)
    print("RESULTS SUMMARY")
    print("=" * 70)
    
    # Without temporal
    passed_no_temp = sum(results_no_temporal)
    total_no_temp = len(results_no_temporal)
    print(f"\nWithout Temporal: {passed_no_temp}/{total_no_temp} passed ({passed_no_temp/total_no_temp*100:.0f}%)")
    
    # With temporal
    passed_with_temp = sum(results_with_temporal)
    total_with_temp = len(results_with_temporal)
    print(f"With Temporal:    {passed_with_temp}/{total_with_temp} passed ({passed_with_temp/total_with_temp*100:.0f}%)")
    
    # Overall
    total_passed = passed_no_temp + passed_with_temp
    total_tests = total_no_temp + total_with_temp
    print(f"\nOverall:          {total_passed}/{total_tests} passed ({total_passed/total_tests*100:.0f}%)")
    print("=" * 70)
    
    return 0 if total_passed == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())