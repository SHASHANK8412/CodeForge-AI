from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:

    def __init__(
        self,
        chunk_size=800,
        chunk_overlap=150
    ):

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                " ",
                ""
            ]
        )

    def split_documents(self, documents):

        chunks = self.splitter.split_documents(documents)

        print("=" * 50)
        print(f"Created {len(chunks)} chunks")
        print("=" * 50)

        return chunks