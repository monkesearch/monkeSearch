#!/usr/bin/env python3
import langextract as lx
import textwrap

class QueryExtractor:
    def __init__(self, model_id="qwen3:0.6b", model_url="http://localhost:11434"):
        self.model_id = model_id
        self.model_url = model_url
        
        self.prompt = textwrap.dedent("""\
            Extract two types of information from search queries:
            FILE TYPE INDICATORS
                REFRAIN FROM giving unrelated filetypes, but give all which can be directly relevant.
               
            TEMPORAL INDICATORS: Time-related expressions with SPECIFIC values only.
               STRICT RULES:
                Only extract when there is an EXPLICIT numeric value or specific time reference
                Assume all time references are from the past (looking backward in time)
                DO NOT extract vague or approximate terms
                DO NOT extract future references
               When extracting, provide two attributes:
                time_unit: The unit of time (days, weeks, months, years, hours, minutes, seconds)
                value: ONLY provide numeric values that are explicitly stated.
               
            DO NOT extract temporal indicators for:
            - Vague approximations: "few", "several", "many", "couple"
            - Any term without a specific numeric value or clear time reference
            
            Use exact text from the query for extraction_text.""")
        
        self.examples = [
            lx.data.ExampleData(
                text="python scripts from three days ago",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="python scripts",
                        attributes={"probable_extensions": "py, ipynb"}
                    ),
                    lx.data.Extraction(
                        extraction_class="temporal_indicator",
                        extraction_text="three days ago",
                        attributes={"time_unit": "days", "value": "3"}
                    ),
                ]
            ),
            lx.data.ExampleData(
                text="old music files",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="music files",
                        attributes={"probable_extensions": "mp3, flac, m4a, wav"}
                    ),
                ]
            ),
            lx.data.ExampleData(
                text="photos from yesterday",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="photos",
                        attributes={"probable_extensions": "jpg, jpeg, png, heic"}
                    ),
                    lx.data.Extraction(
                        extraction_class="temporal_indicator",
                        extraction_text="yesterday",
                        attributes={"time_unit": "days", "value": "1"}
                    ),
                ]
            ),
            lx.data.ExampleData(
                text="pdf invoices from 2023",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="pdf",
                        attributes={"probable_extensions": "pdf"}
                    ),
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="invoices",
                        attributes={"probable_extensions": "pdf, xlsx"}
                    ),
                    lx.data.Extraction(
                        extraction_class="temporal_indicator",
                        extraction_text="2023",
                        attributes={"time_unit": "years", "value": "2023"}
                    ),
                ]
            ),
            lx.data.ExampleData(
                text="resume from last week",
                extractions=[
                    lx.data.Extraction(
                        extraction_class="file_type_indicator",
                        extraction_text="resume",
                        attributes={"probable_extensions": "pdf, docx, doc"}
                    ),
                    lx.data.Extraction(
                        extraction_class="temporal_indicator",
                        extraction_text="last week",
                        attributes={"time_unit": "weeks", "value": "1"}
                    ),
                ]
            )
        ]
    
    def extract(self, query):
        """Extract file types and temporal indicators from query"""
        result = lx.extract(
            text_or_documents=query,
            prompt_description=self.prompt,
            examples=self.examples,
            model_id=self.model_id,
            model_url=self.model_url,
            fence_output=False,
            use_schema_constraints=False,
            max_char_buffer=100,
            extraction_passes=1,
            max_workers=2,
        )
        
        return result
    
    def get_file_types(self, query):
        """Extract only file types from query"""
        result = self.extract(query)
        file_types = []
        extracted_text = []
        
        if result and result.extractions:
            for extraction in result.extractions:
                if extraction.extraction_class == "file_type_indicator":
                    extensions = extraction.attributes.get("probable_extensions", "")
                    file_types.extend([ext.strip() for ext in extensions.split(",")])
                    extracted_text.append(extraction.extraction_text)
        
        return file_types, extracted_text
    
    def get_temporal(self, query):
        """Extract only temporal indicators from query"""
        result = self.extract(query)
        temporal_data = []
        extracted_text = []
        
        if result and result.extractions:
            for extraction in result.extractions:
                if extraction.extraction_class == "temporal_indicator":
                    temporal_data.append({
                        "text": extraction.extraction_text,
                        "time_unit": extraction.attributes.get("time_unit"),
                        "value": extraction.attributes.get("value")
                    })
                    extracted_text.append(extraction.extraction_text)
        
        return temporal_data, extracted_text
    
    def parse_query(self, query):
        """Parse query and return structured data"""
        
        # stop words which will be removed right away, before LLM even gets it.
        STOP_WORDS = {
            'in', 'at', 'of', 'by', 'as', 'me',
            'the', 'a', 'an', 'and', 'any',
            'find', 'search', 'list', 'file', 'files',
            'ago', 'back',
            'past', 'earlier', 'folder'
        }
        words = query.split()
        filtered_words = [word for word in words if word.lower() not in STOP_WORDS]
        cleaned_query = " ".join(filtered_words)
        
        result = self.extract(cleaned_query)
        
        file_types = []
        temporal_data = []
        all_extracted_text = []
        
        if result and result.extractions:
            for extraction in result.extractions:
                if extraction.extraction_class == "file_type_indicator":
                    extensions = extraction.attributes.get("probable_extensions", "")
                    file_types.extend([ext.strip() for ext in extensions.split(",")])
                    all_extracted_text.append(extraction.extraction_text)
                    
                elif extraction.extraction_class == "temporal_indicator":
                    temporal_data.append({
                        "text": extraction.extraction_text,
                        "time_unit": extraction.attributes.get("time_unit"),
                        "value": extraction.attributes.get("value")
                    })
                    all_extracted_text.append(extraction.extraction_text)
        
        # Get remaining text (misc keywords)
        misc_keywords = cleaned_query
        for text in all_extracted_text:
            misc_keywords = misc_keywords.replace(text, "").strip()
        
        # Filter out words with 2 or fewer characters
        if misc_keywords:
            words = misc_keywords.split()
            filtered_words = [word for word in words if len(word) > 2]
            misc_keywords = " ".join(filtered_words)
        
        return {
            "file_types": file_types,
            "temporal": temporal_data,
            "misc_keywords": misc_keywords,
            "original_query": query # original query with stop words, just for reference
        }


# CLI usage if run directly
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("query", type=str)
    args = parser.parse_args()
    
    extractor = QueryExtractor()
    parsed = extractor.parse_query(args.query)
    
    print(f"File types: {parsed['file_types']}")
    print(f"Temporal: {parsed['temporal']}")
    print(f"Misc keywords: {parsed['misc_keywords']}")