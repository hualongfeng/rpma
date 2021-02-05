// SPDX-License-Identifier: BSD-3-Clause
/* Copyright 2020-2021, Intel Corporation */

/*
 * rpma_utils-get_ibv_context.c -- 'get ibv context' multithreaded test
 */

#include <assert.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <pthread.h>

#include <librpma.h>

#define MAX_ADDR (4 * 4 - 1)

struct thread_args {
	int thread_num;
	char addr[MAX_ADDR];
};

static const char *api_name = "rpma_utils_get_ibv_context";

static void *thread_main(void *arg)
{
	int ret;
	/* parameters */
	struct thread_args *p_thread_args = (struct thread_args *)arg;

	/* resources */
	struct ibv_context *dev = NULL;

	/* obtain an IBV context for a local IP address */
	ret = rpma_utils_get_ibv_context(p_thread_args->addr,
			RPMA_UTIL_IBV_CONTEXT_LOCAL, &dev);
	if (ret) {
		fprintf(stderr, "[thread #%d] %s failed: %s\n",
			p_thread_args->thread_num, api_name,
			rpma_err_2str(ret));
		exit(-1);
	}

	return NULL;
}

int
main(int argc, char *argv[])
{
	if (argc < 3) {
		fprintf(stderr, "usage: %s <thread_nums> <addr>\n", argv[0]);
		exit(-1);
	}

	/* configure logging thresholds to see more details */
	rpma_log_set_threshold(RPMA_LOG_THRESHOLD, RPMA_LOG_LEVEL_INFO);
	rpma_log_set_threshold(RPMA_LOG_THRESHOLD_AUX, RPMA_LOG_LEVEL_INFO);

	/* parameters */
	pthread_t *p_threads;
	struct thread_args *threads_args;
	int ret = 0;
	int i;

	int thread_num = (int)strtoul(argv[1], NULL, 10);
	char *addr = argv[2];

	p_threads = calloc((size_t)thread_num, sizeof(pthread_t));
	if (p_threads == NULL) {
		fprintf(stderr, "malloc failed");
		exit(-1);
	}

	threads_args = calloc((size_t)thread_num, sizeof(struct thread_args));
	if (threads_args == NULL) {
		fprintf(stderr, "malloc failed");
		goto err_free_p_threads;
	}

	for (i = 0; i < thread_num; i++) {
		threads_args[i].thread_num = i;
		strncpy(threads_args[i].addr, addr,
			sizeof(threads_args[i].addr) - 1);
		if ((ret = pthread_create(&p_threads[i], NULL, thread_main,
				&threads_args[i])) != 0) {
			fprintf(stderr, "Cannot start a thread #%d: %s\n",
				i, strerror(ret));
			goto err_free_threads_args;
		}
	}

	for (i = thread_num - 1; i >= 0; i--)
		pthread_join(p_threads[i], NULL);

	return 0;

err_free_threads_args:
	free(threads_args);

err_free_p_threads:
	free(p_threads);

	return -1;
}
