"use client";

import { Sidebar } from "@/components/layout/Sidebar";
import { Header } from "@/components/layout/Header";
import { DocumentUploader } from "@/components/admin/DocumentUploader";
import { DocumentTable } from "@/components/admin/DocumentTable";
import { JobStatusPanel } from "@/components/admin/JobStatusPanel";
import { useDocuments } from "@/hooks/useDocuments";
import { Button } from "@/components/ui/Button";
import { RefreshCw } from "lucide-react";

/**
 * Admin document management page.
 * Upload documents, view the document table, and monitor ingestion jobs.
 */
export default function AdminDocumentsPage() {
  const {
    documents,
    isLoading,
    isUploading,
    uploadProgress,
    error,
    uploadDocument,
    deleteDocument,
    refreshDocuments,
  } = useDocuments();

  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header
          title="Document Management"
          subtitle={`${documents.length} documents in knowledge base`}
          actions={
            <Button
              size="sm"
              variant="ghost"
              onClick={refreshDocuments}
              leftIcon={<RefreshCw className="w-4 h-4" />}
            >
              Refresh
            </Button>
          }
        />

        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Upload section */}
          <div className="card p-6">
            <h2 className="text-base font-semibold text-text-primary mb-4">
              Upload New Document
            </h2>
            <DocumentUploader
              onUpload={uploadDocument}
              isUploading={isUploading}
              uploadProgress={uploadProgress}
            />
          </div>

          {/* Two-column layout: Table + Jobs */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Document table */}
            <div className="xl:col-span-2 card p-0 overflow-hidden">
              <div className="px-6 py-4 border-b border-border">
                <h2 className="text-base font-semibold text-text-primary">
                  All Documents
                </h2>
              </div>
              <DocumentTable
                documents={documents}
                isLoading={isLoading}
                onDelete={deleteDocument}
              />
            </div>

            {/* Job status panel */}
            <div className="card p-4">
              <JobStatusPanel documents={documents} />
            </div>
          </div>

          {/* Error toast */}
          {error && (
            <div className="fixed bottom-6 right-6 flex items-center gap-2 px-4 py-3 rounded-xl bg-danger-subtle border border-danger/20 text-danger text-sm shadow-elevated animate-slide-up">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
